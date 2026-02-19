from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.search.models import ClickEvent, SearchEvent
from apps.users.models import User

logger = logging.getLogger(__name__)


class SearchTrackingService:
    @staticmethod
    async def log_search_event(
        db: AsyncSession,
        user: User | None,
        query_text: str,
        filters_json: dict[str, Any] | None,
        top_doc_ids: list[str],
    ) -> None:
        event = SearchEvent(
            user_id=user.id if user else None,
            query_text=query_text,
            role=user.role.value if user else None,
            filters_json=filters_json,
            top_doc_ids=top_doc_ids,
        )
        db.add(event)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.warning("Failed to track search event", exc_info=True)

    @staticmethod
    async def log_click_event(
        db: AsyncSession,
        user: User,
        doc_id: str,
        position: int | None,
        query_text: str | None,
    ) -> None:
        # doc_id is expected in format "type:entity_id" (e.g., "club:50")
        # or as a UUID string from Qdrant
        if ":" in doc_id:
            doc_type, _, entity_id = doc_id.partition(":")
        else:
            # If it's just a UUID, we can't extract type/entity_id
            doc_type = "unknown"
            entity_id = doc_id

        event = ClickEvent(
            user_id=user.id,
            doc_id=doc_id,
            doc_type=doc_type or "unknown",
            entity_id=entity_id or doc_id,
            position=position,
            query_text=query_text,
        )
        db.add(event)
        await db.commit()

    @staticmethod
    async def get_recent_click_events(db: AsyncSession, user_id: int, limit: int = 20) -> list[ClickEvent]:
        result = await db.execute(
            select(ClickEvent)
            .where(ClickEvent.user_id == user_id)
            .order_by(desc(ClickEvent.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_tracked_events_last_24h(db: AsyncSession) -> int:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await db.execute(select(func.count(SearchEvent.id)).where(SearchEvent.created_at >= since))
        return int(result.scalar() or 0)
