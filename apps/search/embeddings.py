from __future__ import annotations

import anyio

from apps.search.config import get_search_settings

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        settings = get_search_settings()
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model


def _encode_sync(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


async def encode_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return await anyio.to_thread.run_sync(_encode_sync, texts)
