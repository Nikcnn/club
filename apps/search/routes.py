from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.settings import settings
from apps.db.dependencies import get_db
from apps.search.config import get_search_settings
from apps.search.qdrant_client import ensure_collection, qdrant_state
from apps.search.schemas import (
    ReindexResponse,
    SearchClickRequest,
    SearchClickResponse,
    SearchHealthResponse,
    SearchResponse,
)
from apps.search.service import SearchService
from apps.search.tracking import SearchTrackingService
from apps.search.personalization import compute_user_preferences
from apps.users.models import User

router = APIRouter(prefix="/search", tags=["Search"])

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


async def allow_all() -> bool:
    return True


async def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "access":
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).where(User.id == int(user_id), User.is_active.is_(True)))
    return result.scalars().first()


async def get_required_current_user(user: User | None = Depends(get_optional_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@router.get("/health", response_model=SearchHealthResponse)
async def search_health(db: AsyncSession = Depends(get_db)) -> SearchHealthResponse:
    search_settings = get_search_settings()
    await ensure_collection()
    tracked_last_day = await SearchTrackingService.count_tracked_events_last_24h(db)

    return SearchHealthResponse(
        qdrant_reachable=qdrant_state.reachable,
        collection_exists=qdrant_state.collection_exists,
        embedding_model=search_settings.EMBEDDING_MODEL_NAME,
        personalization_enabled=search_settings.PERSONALIZATION_ENABLED,
        tracked_events_last_24h=tracked_last_day,
        last_profile_build=None,
        last_error=qdrant_state.last_error,
    )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_search(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(allow_all),
) -> ReindexResponse:
    indexed = await SearchService.rebuild_index(db)
    return ReindexResponse(indexed=indexed)


@router.post("/click", response_model=SearchClickResponse)
async def track_click(
    payload: SearchClickRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_current_user),
) -> SearchClickResponse:
    await SearchTrackingService.log_click_event(
        db,
        user=current_user,
        doc_id=payload.doc_id,
        position=payload.position,
        query_text=payload.query_text,
    )
    return SearchClickResponse(ok=True)


@router.get("/recommend", response_model=SearchResponse)
async def recommend(
    top_k: int = Query(10, ge=1, le=50),
    type: Literal["club", "campaign", "news"] | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_current_user),
) -> SearchResponse:
    recent_clicks = await SearchTrackingService.get_recent_click_events(db, current_user.id, limit=20)

    # Convert doc_ids from "type:entity_id" format to UUIDs for Qdrant
    clicked_doc_ids = []
    for click in recent_clicks:
        # Always reconstruct UUID from doc_type and entity_id stored in DB
        uuid_doc_id = SearchService.build_doc_id(click.doc_type, click.entity_id)
        clicked_doc_ids.append(uuid_doc_id)

    if clicked_doc_ids:
        vectors = await SearchService.fetch_vectors_by_doc_ids(clicked_doc_ids)
        profile_vector = SearchService.build_profile_vector(vectors)
        if profile_vector:
            items = await SearchService.recommend_by_profile_vector(
                profile_vector=profile_vector,
                top_k=top_k,
                doc_type=type,
                exclude_doc_ids=clicked_doc_ids,
            )
            return SearchResponse(total=len(items), items=items)

    fallback_items = await SearchService.fallback_recommendations(
        db=db,
        user_role=current_user.role.value,
        top_k=top_k,
        doc_type=type,
    )
    return SearchResponse(total=len(fallback_items), items=fallback_items)


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2),
    top_k: int = Query(10, ge=1, le=50),
    type: Literal["club", "campaign", "news"] | None = Query(None),
    city: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    personalize: bool | None = Query(None),
    role_boost: bool = Query(True),
    track: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> SearchResponse:
    search_settings = get_search_settings()
    is_authenticated = current_user is not None

    personalize_effective = bool(search_settings.PERSONALIZATION_ENABLED and is_authenticated)
    if personalize is not None:
        personalize_effective = bool(personalize and is_authenticated and search_settings.PERSONALIZATION_ENABLED)

    track_effective = bool(is_authenticated)
    if track is not None:
        track_effective = bool(track and is_authenticated)

    raw_items = await SearchService.semantic_search(
        q=q,
        top_k=top_k,
        doc_type=type,
        city=city,
        category=category,
        status=status,
    )

    if personalize_effective and current_user is not None:
        recent_clicks = await SearchTrackingService.get_recent_click_events(db, current_user.id, limit=50)
        preferences = compute_user_preferences(
            [
                {"doc_type": click.doc_type}
                for click in recent_clicks
            ]
        )
        raw_items = SearchService.personalize_results(
            raw_items,
            user_role=current_user.role.value,
            preferences=preferences,
            role_boost=role_boost,
        )

    if track_effective:
        filters_json = {
            "type": type,
            "city": city,
            "category": category,
            "status": status,
            "personalize": personalize_effective,
            "role_boost": role_boost,
        }
        await SearchTrackingService.log_search_event(
            db=db,
            user=current_user,
            query_text=q,
            filters_json=filters_json,
            top_doc_ids=[item.get("doc_id") for item in raw_items if item.get("doc_id")],
        )

    response_items = [
        {
            "type": item.get("type", "unknown"),
            "entity_id": item.get("entity_id"),
            "title": item.get("title", ""),
            "snippet": item.get("snippet"),
            "url": item.get("url"),
            "score": float(item.get("score", 0.0)),
        }
        for item in raw_items
    ]

    return SearchResponse(total=len(response_items), items=response_items)
