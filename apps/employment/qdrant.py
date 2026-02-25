from __future__ import annotations

import logging
from typing import Any

from qdrant_client.http.models import Distance, PointStruct, VectorParams

from apps.employment.ai_service import EmploymentAIService
from apps.search.qdrant_client import get_qdrant_client, search_points
from apps.core.settings import settings

logger = logging.getLogger(__name__)


async def ensure_employment_collection() -> bool:
    client = get_qdrant_client()
    try:
        exists = await client.collection_exists(settings.EMPLOYMENT_QDRANT_COLLECTION)
        if not exists:
            await client.create_collection(
                collection_name=settings.EMPLOYMENT_QDRANT_COLLECTION,
                vectors_config=VectorParams(size=64, distance=Distance.COSINE),
            )
        return True
    except Exception as exc:
        logger.warning("Employment Qdrant unavailable: %s", exc)
        return False


async def upsert_candidate_vector(candidate_id: int, payload: dict[str, Any]) -> None:
    if not await ensure_employment_collection():
        return
    client = get_qdrant_client()
    vector = EmploymentAIService.vectorize(payload)
    await client.upsert(
        collection_name=settings.EMPLOYMENT_QDRANT_COLLECTION,
        points=[PointStruct(id=f"candidate:{candidate_id}", vector=vector, payload={"type": "candidate", "entity_id": candidate_id})],
    )


async def upsert_vacancy_vector(vacancy_id: int, payload: dict[str, Any]) -> None:
    if not await ensure_employment_collection():
        return
    client = get_qdrant_client()
    vector = EmploymentAIService.vectorize(payload)
    await client.upsert(
        collection_name=settings.EMPLOYMENT_QDRANT_COLLECTION,
        points=[PointStruct(id=f"vacancy:{vacancy_id}", vector=vector, payload={"type": "vacancy", "entity_id": vacancy_id})],
    )


async def search_candidates_for_vacancy(vacancy_payload: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    if not await ensure_employment_collection():
        return []
    vector = EmploymentAIService.vectorize(vacancy_payload)
    hits = await search_points(
        collection_name=settings.EMPLOYMENT_QDRANT_COLLECTION,
        query_vector=vector,
        query_filter=None,
        limit=limit,
        score_threshold=None,
        with_payload=True,
    )
    return [hit.payload for hit in hits if (hit.payload or {}).get("type") == "candidate"]


async def search_vacancies_for_candidate(candidate_payload: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    if not await ensure_employment_collection():
        return []
    vector = EmploymentAIService.vectorize(candidate_payload)
    hits = await search_points(
        collection_name=settings.EMPLOYMENT_QDRANT_COLLECTION,
        query_vector=vector,
        query_filter=None,
        limit=limit,
        score_threshold=None,
        with_payload=True,
    )
    return [hit.payload for hit in hits if (hit.payload or {}).get("type") == "vacancy"]
