import logging

import httpx

from apps.core.settings import settings
from apps.reviews.models import ModerationStatus

logger = logging.getLogger(__name__)

PERSPECTIVE_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
PERSPECTIVE_ATTRIBUTES = (
    "TOXICITY",
    "SEVERE_TOXICITY",
    "INSULT",
    "PROFANITY",
    "THREAT",
    "IDENTITY_ATTACK",
)

# Safety-net for obvious slurs when provider is unavailable/misconfigured.
LOCAL_BLOCKLIST = {
    "fagot": 0.99,
    "faggot": 0.99,
}


class ModerationService:
    @staticmethod
    async def analyze_text(text: str) -> tuple[float, dict]:
        local_toxicity, local_labels = ModerationService._local_signal(text)
        if local_toxicity > 0:
            status, _ = ModerationService.decide_status(local_toxicity)
            if status == ModerationStatus.REJECTED.value:
                return local_toxicity, local_labels

        if not settings.MODERATION_ENABLED:
            return ModerationService._fallback_result()

        if settings.MODERATION_PROVIDER != "perspective":
            logger.warning("Unknown moderation provider '%s', using fallback", settings.MODERATION_PROVIDER)
            return ModerationService._fallback_result(extra_labels=local_labels)

        if not settings.PERSPECTIVE_API_KEY:
            logger.warning("PERSPECTIVE_API_KEY is empty, using fallback moderation strategy")
            return ModerationService._fallback_result(extra_labels=local_labels)

        payload = {
            "comment": {"text": text},
            "languages": ["ru", "en"],
            "requestedAttributes": {attribute: {} for attribute in PERSPECTIVE_ATTRIBUTES},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    PERSPECTIVE_URL,
                    params={"key": settings.PERSPECTIVE_API_KEY},
                    json=payload,
                )
                response.raise_for_status()
        except Exception as exc:
            logger.exception("Moderation provider call failed: %s", exc)
            return ModerationService._fallback_result(extra_labels=local_labels)

        body = response.json()
        scores: dict[str, float] = {}

        for attribute in PERSPECTIVE_ATTRIBUTES:
            value = (
                body.get("attributeScores", {})
                .get(attribute, {})
                .get("summaryScore", {})
                .get("value")
            )
            if isinstance(value, (int, float)):
                scores[attribute] = float(value)

        if not scores:
            logger.warning("Perspective API returned empty scores, using fallback strategy")
            return ModerationService._fallback_result(extra_labels=local_labels)

        toxicity = max(scores.values(), default=0.0)
        scores.update(local_labels)
        return toxicity, scores

    @staticmethod
    def decide_status(toxicity: float) -> tuple[str, bool]:
        if toxicity >= settings.TOXICITY_THRESHOLD_REJECT:
            return ModerationStatus.REJECTED.value, False

        if toxicity >= settings.TOXICITY_THRESHOLD_PENDING:
            return ModerationStatus.PENDING.value, False

        return ModerationStatus.APPROVED.value, True

    @staticmethod
    def _fallback_result(extra_labels: dict | None = None) -> tuple[float, dict]:
        labels = extra_labels.copy() if extra_labels else {}

        if labels:
            max_local = max(v for v in labels.values() if isinstance(v, (int, float)))
            status, _ = ModerationService.decide_status(max_local)
            if status == ModerationStatus.REJECTED.value:
                labels["fallback"] = "local_blocklist"
                return max_local, labels

        if settings.MODERATION_FAIL_MODE == "pending":
            labels["fallback"] = "pending"
            return settings.TOXICITY_THRESHOLD_PENDING, labels

        labels["fallback"] = "approve"
        return 0.0, labels



    @staticmethod
    async def provider_healthcheck() -> dict:
        if not settings.MODERATION_ENABLED:
            return {"ok": False, "state": "disabled", "provider": settings.MODERATION_PROVIDER}

        if settings.MODERATION_PROVIDER != "perspective":
            return {"ok": False, "state": "unsupported_provider", "provider": settings.MODERATION_PROVIDER}

        if not settings.PERSPECTIVE_API_KEY:
            return {"ok": False, "state": "missing_api_key", "provider": "perspective"}

        payload = {
            "comment": {"text": "healthcheck"},
            "languages": ["en"],
            "requestedAttributes": {"TOXICITY": {}},
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    PERSPECTIVE_URL,
                    params={"key": settings.PERSPECTIVE_API_KEY},
                    json=payload,
                )

            if response.status_code >= 400:
                return {
                    "ok": False,
                    "state": "provider_error",
                    "provider": "perspective",
                    "http_status": response.status_code,
                }

            return {"ok": True, "state": "ok", "provider": "perspective"}
        except Exception as exc:
            logger.exception("Moderation healthcheck failed: %s", exc)
            return {
                "ok": False,
                "state": "request_failed",
                "provider": "perspective",
                "error": str(exc),
            }

    @staticmethod
    def _local_signal(text: str) -> tuple[float, dict]:
        if not text:
            return 0.0, {}

        normalized = text.lower()
        matched = {f"LOCAL_{word.upper()}": score for word, score in LOCAL_BLOCKLIST.items() if word in normalized}
        if not matched:
            return 0.0, {}

        return max(matched.values()), matched
