import json
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

GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

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
            return ModerationService._fallback_result(extra_labels=local_labels)

        provider = settings.MODERATION_PROVIDER.strip().lower()

        if provider == "perspective":
            return await ModerationService._analyze_with_perspective(text, local_labels)
        if provider == "gemini":
            return await ModerationService._analyze_with_gemini(text, local_labels)

        logger.warning("Unknown moderation provider '%s', using fallback", settings.MODERATION_PROVIDER)
        return ModerationService._fallback_result(extra_labels=local_labels)

    @staticmethod
    async def _analyze_with_perspective(text: str, local_labels: dict) -> tuple[float, dict]:
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

            if response.status_code >= 400:
                provider_error = ModerationService._extract_provider_error(response)
                logger.warning(
                    "Moderation provider returned %s: %s",
                    response.status_code,
                    provider_error or "unknown error",
                )
                labels = local_labels.copy()
                labels["provider_http_status"] = response.status_code
                if provider_error:
                    labels["provider_error"] = provider_error
                return ModerationService._fallback_result(extra_labels=labels)
        except Exception as exc:
            logger.exception("Moderation provider call failed: %s", exc)
            labels = local_labels.copy()
            labels["provider_error"] = str(exc)
            return ModerationService._fallback_result(extra_labels=labels)

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
    async def _analyze_with_gemini(text: str, local_labels: dict) -> tuple[float, dict]:
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is empty, using fallback moderation strategy")
            return ModerationService._fallback_result(extra_labels=local_labels)

        prompt = (
            "You are a moderation classifier. Return ONLY JSON with keys: "
            "toxicity (number from 0 to 1) and labels (object with numeric scores 0..1). "
            "Classify harassment/toxicity/insult/profanity/threat/identity_attack for this text: "
            f"{text}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }

        url = GEMINI_URL_TEMPLATE.format(model=settings.GEMINI_MODEL)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, params={"key": settings.GEMINI_API_KEY}, json=payload)

            if response.status_code >= 400:
                provider_error = ModerationService._extract_provider_error(response)
                logger.warning("Gemini moderation returned %s: %s", response.status_code, provider_error)
                labels = local_labels.copy()
                labels["provider_http_status"] = response.status_code
                if provider_error:
                    labels["provider_error"] = provider_error
                return ModerationService._fallback_result(extra_labels=labels)

            data = response.json()
            text_payload = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if not text_payload:
                return ModerationService._fallback_result(extra_labels=local_labels)

            parsed = json.loads(text_payload)
            toxicity = float(parsed.get("toxicity", 0.0))
            labels = parsed.get("labels", {}) if isinstance(parsed.get("labels", {}), dict) else {}
            clean_labels = {k: float(v) for k, v in labels.items() if isinstance(v, (int, float))}
            clean_labels.update(local_labels)
            return min(max(toxicity, 0.0), 1.0), clean_labels
        except Exception as exc:
            logger.exception("Gemini moderation call failed: %s", exc)
            labels = local_labels.copy()
            labels["provider_error"] = str(exc)
            return ModerationService._fallback_result(extra_labels=labels)

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
            numeric_values = [v for v in labels.values() if isinstance(v, (int, float))]
            if numeric_values:
                max_local = max(numeric_values)
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

        provider = settings.MODERATION_PROVIDER.strip().lower()
        if provider == "perspective":
            return await ModerationService._perspective_healthcheck()
        if provider == "gemini":
            return await ModerationService._gemini_healthcheck()

        return {"ok": False, "state": "unsupported_provider", "provider": settings.MODERATION_PROVIDER}

    @staticmethod
    async def _perspective_healthcheck() -> dict:
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
                    "error": ModerationService._extract_provider_error(response),
                }

            return {"ok": True, "state": "ok", "provider": "perspective"}
        except Exception as exc:
            logger.exception("Moderation healthcheck failed: %s", exc)
            return {"ok": False, "state": "request_failed", "provider": "perspective", "error": str(exc)}

    @staticmethod
    async def _gemini_healthcheck() -> dict:
        if not settings.GEMINI_API_KEY:
            return {"ok": False, "state": "missing_api_key", "provider": "gemini"}

        url = GEMINI_URL_TEMPLATE.format(model=settings.GEMINI_MODEL)
        payload = {
            "contents": [{"parts": [{"text": "Return JSON: {\"toxicity\":0,\"labels\":{}}"}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(url, params={"key": settings.GEMINI_API_KEY}, json=payload)

            if response.status_code >= 400:
                return {
                    "ok": False,
                    "state": "provider_error",
                    "provider": "gemini",
                    "http_status": response.status_code,
                    "error": ModerationService._extract_provider_error(response),
                }
            return {"ok": True, "state": "ok", "provider": "gemini"}
        except Exception as exc:
            logger.exception("Gemini healthcheck failed: %s", exc)
            return {"ok": False, "state": "request_failed", "provider": "gemini", "error": str(exc)}

    @staticmethod
    def _local_signal(text: str) -> tuple[float, dict]:
        if not text:
            return 0.0, {}

        normalized = text.lower()
        matched = {f"LOCAL_{word.upper()}": score for word, score in LOCAL_BLOCKLIST.items() if word in normalized}
        if not matched:
            return 0.0, {}

        return max(matched.values()), matched

    @staticmethod
    def _extract_provider_error(response: httpx.Response) -> str | None:
        try:
            body = response.json()
        except Exception:
            return response.text[:300] if response.text else None

        error_obj = body.get("error") if isinstance(body, dict) else None
        if isinstance(error_obj, dict):
            message = error_obj.get("message")
            if isinstance(message, str):
                return message

        if isinstance(body, dict):
            message = body.get("message")
            if isinstance(message, str):
                return message

        return response.text[:300] if response.text else None
