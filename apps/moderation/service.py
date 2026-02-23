import json
import logging
import re

import httpx

from apps.core.settings import settings
from apps.reviews.models import ModerationStatus

logger = logging.getLogger(__name__)


class ModerationService:
    @staticmethod
    async def analyze_text(text: str) -> tuple[float, dict]:
        if not settings.MODERATION_ENABLED:
            return ModerationService._fallback_result()

        if settings.MODERATION_PROVIDER.lower() != "openrouter":
            logger.warning("Unsupported moderation provider '%s'", settings.MODERATION_PROVIDER)
            return ModerationService._fallback_result()

        if not settings.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY is not configured")
            return ModerationService._fallback_result()

        payload = {
            "model": settings.OPENROUTER_MODEL_NAME,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a moderation classifier. "
                        "Respond ONLY with JSON object containing keys: "
                        "toxicity_score (number from 0 to 1), labels (object), reason (string)."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this user-generated text for toxicity and abuse: {text}",
                },
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    ModerationService._openrouter_endpoint(),
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
            raw_content = body["choices"][0]["message"]["content"]
            normalized_content = ModerationService._normalize_content(raw_content)
            parsed = ModerationService._parse_model_json(normalized_content)

            toxicity = float(parsed.get("toxicity_score", 0.0))
            toxicity = max(0.0, min(1.0, toxicity))

            labels = parsed.get("labels")
            labels = labels if isinstance(labels, dict) else {}

            reason = parsed.get("reason")
            if reason is not None:
                labels["reason"] = str(reason)

            return toxicity, labels
        except Exception as exc:
            logger.exception("Failed to parse moderation response: %s", exc)
            return ModerationService._fallback_result()

    @staticmethod
    def _openrouter_endpoint() -> str:
        base = settings.OPENROUTER_BASE_URL.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"


    @staticmethod
    def _normalize_content(content: str | list | dict) -> str | dict:
        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                    continue

                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
            if chunks:
                return "\n".join(chunks)

        raise ValueError("Unsupported model response content format")

    @staticmethod
    def _parse_model_json(content: str | dict) -> dict:
        if isinstance(content, dict):
            return content

        if not isinstance(content, str):
            raise ValueError("Model response content is not a string")

        text = content.strip()

        if text.startswith("```"):
            fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S | re.I)
            if fenced:
                text = fenced.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.S)
            if not match:
                raise
            return json.loads(match.group(0))

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
