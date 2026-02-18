from __future__ import annotations

import logging
from typing import Any
import uuid as uuid_module

from fastapi import HTTPException
from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    HasIdCondition,
    MatchValue,
    PointIdsList,
    PointStruct,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clubs.models import Club
from apps.funding.models import Campaign, CampaignStatus
from apps.news.models import News
from apps.search.config import get_search_settings
from apps.search.embeddings import encode_texts
from apps.search.personalization import BonusWeights, build_profile_vector, rerank_results
from apps.search.qdrant_client import ensure_collection, get_qdrant_client, search_points

logger = logging.getLogger(__name__)


class SearchService:
    @staticmethod
    def build_doc_id(doc_type: str, entity_id: Any) -> str:
        return str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, f"{doc_type}:{entity_id}"))

    @staticmethod
    def build_text(payload: dict[str, Any]) -> str:
        chunks = [
            payload.get("title"),
            payload.get("snippet"),
            payload.get("city"),
            payload.get("category"),
            payload.get("status"),
        ]
        return " ".join(str(chunk).strip() for chunk in chunks if chunk)

    @staticmethod
    def club_payload(club: Club) -> dict[str, Any]:
        return {
            "type": "club",
            "entity_id": club.id,
            "title": club.name,
            "snippet": club.description,
            "url": f"/clubs/{club.id}",
            "city": club.city,
            "category": club.category,
            "status": None,
        }

    @staticmethod
    def campaign_payload(campaign: Campaign) -> dict[str, Any]:
        return {
            "type": "campaign",
            "entity_id": campaign.id,
            "title": campaign.title,
            "snippet": campaign.description,
            "url": f"/funding/campaigns/{campaign.id}/",
            "city": None,
            "category": None,
            "status": campaign.status.value if campaign.status else None,
        }

    @staticmethod
    def news_payload(news: News) -> dict[str, Any]:
        return {
            "type": "news",
            "entity_id": news.id,
            "title": news.title,
            "snippet": news.body,
            "url": f"/news/{news.id}",
            "city": None,
            "category": None,
            "status": "published" if news.is_published else "draft",
        }

    @staticmethod
    async def fetch_clubs(db: AsyncSession) -> list[dict[str, Any]]:
        result = await db.execute(select(Club))
        return [SearchService.club_payload(club) for club in result.scalars().all()]

    @staticmethod
    async def fetch_campaigns(db: AsyncSession) -> list[dict[str, Any]]:
        result = await db.execute(select(Campaign))
        return [SearchService.campaign_payload(campaign) for campaign in result.scalars().all()]

    @staticmethod
    async def fetch_news(db: AsyncSession) -> list[dict[str, Any]]:
        result = await db.execute(select(News))
        return [SearchService.news_payload(news) for news in result.scalars().all()]

    @staticmethod
    async def rebuild_index(db: AsyncSession) -> int:
        ready = await ensure_collection()
        if not ready:
            raise HTTPException(status_code=503, detail="Qdrant is unavailable. Please retry later.")

        docs = [
            *await SearchService.fetch_clubs(db),
            *await SearchService.fetch_campaigns(db),
            *await SearchService.fetch_news(db),
        ]
        vectors = await encode_texts([SearchService.build_text(doc) for doc in docs])

        points = []
        for doc, vector in zip(docs, vectors, strict=False):
            doc_id = SearchService.build_doc_id(doc["type"], doc["entity_id"])
            payload = {
                **doc,
                "entity_id": str(doc["entity_id"]),
                "doc_id": doc_id,
                "text": SearchService.build_text(doc),
            }
            points.append(PointStruct(id=doc_id, vector=vector, payload=payload))

        if points:
            client = get_qdrant_client()
            settings = get_search_settings()
            await client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)

        logger.info("Reindexed %s documents", len(points))
        return len(points)

    @staticmethod
    async def upsert_single(payload: dict[str, Any]) -> None:
        ready = await ensure_collection()
        if not ready:
            logger.warning("Skip upsert: Qdrant unavailable")
            return

        vectors = await encode_texts([SearchService.build_text(payload)])
        if not vectors:
            return

        doc_id = SearchService.build_doc_id(payload["type"], payload["entity_id"])
        point = PointStruct(
            id=doc_id,
            vector=vectors[0],
            payload={
                **payload,
                "entity_id": str(payload["entity_id"]),
                "doc_id": doc_id,
                "text": SearchService.build_text(payload),
            },
        )
        client = get_qdrant_client()
        settings = get_search_settings()
        await client.upsert(collection_name=settings.QDRANT_COLLECTION, points=[point])

    @staticmethod
    async def delete_point(doc_type: str, entity_id: Any) -> None:
        ready = await ensure_collection()
        if not ready:
            logger.warning("Skip delete: Qdrant unavailable")
            return

        client = get_qdrant_client()
        settings = get_search_settings()
        await client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=PointIdsList(points=[SearchService.build_doc_id(doc_type, entity_id)]),
        )

    @staticmethod
    def _build_filter(
        doc_type: str | None = None,
        city: str | None = None,
        category: str | None = None,
        status: str | None = None,
        exclude_doc_ids: list[str] | None = None,
    ) -> Filter | None:
        must: list[FieldCondition] = []
        must_not: list[HasIdCondition] = []

        if doc_type:
            must.append(FieldCondition(key="type", match=MatchValue(value=doc_type)))
        if city:
            must.append(FieldCondition(key="city", match=MatchValue(value=city)))
        if category:
            must.append(FieldCondition(key="category", match=MatchValue(value=category)))
        if status:
            must.append(FieldCondition(key="status", match=MatchValue(value=status)))
        if exclude_doc_ids:
            # Convert string UUIDs to UUID objects for Qdrant
            uuid_list = [uuid_module.UUID(doc_id) if isinstance(doc_id, str) else doc_id for doc_id in exclude_doc_ids]
            must_not.append(HasIdCondition(has_id=uuid_list))

        if not must and not must_not:
            return None
        return Filter(must=must or None, must_not=must_not or None)

    @staticmethod
    def _normalize_hit(hit: Any) -> dict[str, Any]:
        payload = hit.payload or {}
        entity_id = payload.get("entity_id")
        if isinstance(entity_id, str) and entity_id.isdigit():
            entity_id = int(entity_id)

        return {
            "doc_id": payload.get("doc_id"),
            "type": payload.get("type", "unknown"),
            "entity_id": entity_id,
            "title": payload.get("title", ""),
            "snippet": payload.get("snippet"),
            "url": payload.get("url"),
            "score": float(hit.score),
            "city": payload.get("city"),
            "category": payload.get("category"),
            "status": payload.get("status"),
        }

    @staticmethod
    async def semantic_search(
        q: str,
        top_k: int,
        doc_type: str | None = None,
        city: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        ready = await ensure_collection()
        if not ready:
            raise HTTPException(status_code=503, detail="Search service is temporarily unavailable.")

        settings = get_search_settings()
        vector = (await encode_texts([q]))[0]
        query_filter = SearchService._build_filter(doc_type=doc_type, city=city, category=category, status=status)

        hits = await search_points(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=settings.SEARCH_SCORE_THRESHOLD,
            with_payload=True,
        )
        return [SearchService._normalize_hit(hit) for hit in hits]

    @staticmethod
    def personalize_results(
        items: list[dict[str, Any]],
        user_role: str | None,
        preferences: dict[str, Any],
        role_boost: bool,
    ) -> list[dict[str, Any]]:
        settings = get_search_settings()
        weights = BonusWeights(
            role_boost_weight=settings.ROLE_BOOST_WEIGHT,
            pref_city_weight=settings.PREF_CITY_WEIGHT,
            pref_category_weight=settings.PREF_CATEGORY_WEIGHT,
            pref_type_weight=settings.PREF_TYPE_WEIGHT,
        )
        return rerank_results(items, user_role=user_role, preferences=preferences, weights=weights, role_boost=role_boost)

    @staticmethod
    async def fetch_vectors_by_doc_ids(doc_ids: list[str]) -> list[list[float]]:
        if not doc_ids:
            return []
        ready = await ensure_collection()
        if not ready:
            raise HTTPException(status_code=503, detail="Search service is temporarily unavailable.")

        client = get_qdrant_client()
        settings = get_search_settings()
        points = await client.retrieve(
            collection_name=settings.QDRANT_COLLECTION,
            ids=doc_ids,
            with_vectors=True,
            with_payload=False,
        )
        vectors: list[list[float]] = []
        for point in points:
            if isinstance(point.vector, list):
                vectors.append([float(v) for v in point.vector])
        return vectors

    @staticmethod
    async def recommend_by_profile_vector(
        profile_vector: list[float],
        top_k: int,
        doc_type: str | None,
        exclude_doc_ids: list[str],
    ) -> list[dict[str, Any]]:
        ready = await ensure_collection()
        if not ready:
            raise HTTPException(status_code=503, detail="Search service is temporarily unavailable.")

        settings = get_search_settings()
        hits = await search_points(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=profile_vector,
            query_filter=SearchService._build_filter(doc_type=doc_type, exclude_doc_ids=exclude_doc_ids),
            limit=top_k,
            score_threshold=settings.SEARCH_SCORE_THRESHOLD,
            with_payload=True,
        )
        return [SearchService._normalize_hit(hit) for hit in hits]

    @staticmethod
    async def fallback_recommendations(db: AsyncSession, user_role: str | None, top_k: int, doc_type: str | None) -> list[dict[str, Any]]:
        if doc_type == "campaign" or user_role == "investor":
            result = await db.execute(
                select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE).limit(top_k)
            )
            campaigns = result.scalars().all()
            return [
                {
                    "doc_id": SearchService.build_doc_id("campaign", item.id),
                    "type": "campaign",
                    "entity_id": item.id,
                    "title": item.title,
                    "snippet": item.description,
                    "url": f"/funding/campaigns/{item.id}/",
                    "score": 0.0,
                }
                for item in campaigns
            ]

        result = await db.execute(select(Club).limit(top_k))
        clubs = result.scalars().all()
        return [
            {
                "doc_id": SearchService.build_doc_id("club", item.id),
                "type": "club",
                "entity_id": item.id,
                "title": item.name,
                "snippet": item.description,
                "url": f"/clubs/{item.id}",
                "score": 0.0,
            }
            for item in clubs
        ]

    @staticmethod
    def build_profile_vector(vectors: list[list[float]]) -> list[float]:
        return build_profile_vector(vectors)
