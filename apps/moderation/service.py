import json
import logging

import httpx

from apps.core.settings import settings
from apps.reviews.models import ModerationStatus

logger = logging.getLogger(__name__)


class ModerationService:
    @staticmethod
    async def analyze_text(text: str) -> tuple[float, dict]:
        if not settings.MODERATION_ENABLED or not settings.OPENROUTER_API_KEY:
            return ModerationService._fallback_result()

        payload = {
            "model": settings.OPENROUTER_MODERATION_MODEL,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a moderation classifier. "
                        "Return only JSON with keys: toxicity_score (0..1), "
                        "labels (object with boolean flags), reason (string)."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this text for policy violations: {text}",
                },
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except Exception as exc:
            logger.exception("Moderation provider call failed: %s", exc)
            return ModerationService._fallback_result()

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            toxicity = float(parsed.get("toxicity_score", 0.0))
            toxicity = max(0.0, min(1.0, toxicity))
            labels = parsed.get("labels") if isinstance(parsed.get("labels"), dict) else {}
            reason = parsed.get("reason")
            if reason is not None:
                labels["reason"] = str(reason)
            return toxicity, labels
        except Exception as exc:
            logger.exception("Failed to parse moderation response: %s", exc)
            return ModerationService._fallback_result()

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
