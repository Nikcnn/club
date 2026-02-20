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


class ModerationService:
    @staticmethod
    async def analyze_text(text: str) -> tuple[float, dict]:
        if not settings.MODERATION_ENABLED or not settings.PERSPECTIVE_API_KEY:
            return ModerationService._fallback_result()

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
            return ModerationService._fallback_result()

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

        toxicity = max(scores.values(), default=0.0)
        return toxicity, scores

    @staticmethod
    def decide_status(toxicity: float) -> tuple[str, bool]:
        if toxicity >= settings.TOXICITY_THRESHOLD_REJECT:
            return ModerationStatus.REJECTED.value, False

        if toxicity >= settings.TOXICITY_THRESHOLD_PENDING:
            return ModerationStatus.PENDING.value, False

        return ModerationStatus.APPROVED.value, True

    @staticmethod
    def _fallback_result() -> tuple[float, dict]:
        if settings.MODERATION_FAIL_MODE == "pending":
            return settings.TOXICITY_THRESHOLD_PENDING, {"fallback": "pending"}

        return 0.0, {"fallback": "approve"}
