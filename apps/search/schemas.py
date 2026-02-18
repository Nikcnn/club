from datetime import datetime

from pydantic import BaseModel


class SearchHit(BaseModel):
    type: str
    entity_id: int | str
    title: str
    snippet: str | None = None
    url: str | None = None
    score: float


class SearchResponse(BaseModel):
    total: int
    items: list[SearchHit]


class ReindexResponse(BaseModel):
    indexed: int


class SearchHealthResponse(BaseModel):
    qdrant_reachable: bool
    collection_exists: bool
    embedding_model: str
    personalization_enabled: bool
    tracked_events_last_24h: int
    last_profile_build: datetime | None = None
    last_error: str | None = None


class SearchClickRequest(BaseModel):
    doc_id: str
    position: int | None = None
    query_text: str | None = None


class SearchClickResponse(BaseModel):
    ok: bool
