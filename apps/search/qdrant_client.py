import inspect
import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import exceptions as qdrant_exceptions
from qdrant_client.http.models import Distance, Filter, VectorParams

from apps.search.config import get_search_settings

logger = logging.getLogger(__name__)


class QdrantState:
    def __init__(self) -> None:
        self.reachable: bool = False
        self.collection_exists: bool = False
        self.last_error: str | None = None


qdrant_state = QdrantState()
_qdrant_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_search_settings()
        _qdrant_client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=5.0,
        )
    return _qdrant_client


async def _call_async(func: Any, **kwargs: Any) -> Any:
    params = inspect.signature(func).parameters
    filtered = {key: value for key, value in kwargs.items() if key in params}
    return await func(**filtered)


async def search_points(
    *,
    collection_name: str,
    query_vector: list[float],
    query_filter: Filter | None,
    limit: int,
    score_threshold: float | None,
    with_payload: bool,
) -> list[Any]:
    client = get_qdrant_client()
    kwargs = {
        "collection_name": collection_name,
        "query_vector": query_vector,
        "query_filter": query_filter,
        "filter": query_filter,
        "query": query_vector,
        "limit": limit,
        "score_threshold": score_threshold,
        "with_payload": with_payload,
    }
    if hasattr(client, "search"):
        return await _call_async(client.search, **kwargs)
    if hasattr(client, "search_points"):
        response = await _call_async(client.search_points, **kwargs)
    elif hasattr(client, "query_points"):
        response = await _call_async(client.query_points, **kwargs)
    else:
        raise AttributeError("AsyncQdrantClient has no search-like method.")
    return response.points if hasattr(response, "points") else response


async def ensure_collection() -> bool:
    settings = get_search_settings()
    client = get_qdrant_client()
    vector_size = settings.VECTOR_SIZE or 384

    try:
        exists = await client.collection_exists(settings.QDRANT_COLLECTION)
        qdrant_state.reachable = True

        if not exists:
            await client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(
                "Qdrant collection '%s' created with vector size %s",
                settings.QDRANT_COLLECTION,
                vector_size,
            )
            qdrant_state.collection_exists = True
        else:
            qdrant_state.collection_exists = True
        qdrant_state.last_error = None
        return True
    except (qdrant_exceptions.ResponseHandlingException, OSError, Exception) as exc:
        qdrant_state.reachable = False
        qdrant_state.collection_exists = False
        qdrant_state.last_error = str(exc)
        logger.warning("Qdrant is not reachable during startup. Search is degraded: %s", exc)
        return False
