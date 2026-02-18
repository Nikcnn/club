from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from apps.db.base import Base


class SearchEvent(Base):
    __tablename__ = "search_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    query_text: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filters_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    top_doc_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    query_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class UserSearchProfile(Base):
    __tablename__ = "user_search_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    top_cities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    top_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    top_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
