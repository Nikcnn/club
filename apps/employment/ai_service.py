from __future__ import annotations

import json
import logging
from hashlib import sha256
from typing import Any

import httpx

from apps.core.settings import settings
from apps.employment.enums import MatchConfidence

logger = logging.getLogger(__name__)


class EmploymentAIService:
    @staticmethod
    def normalize_text(payload: dict[str, Any]) -> str:
        return " ".join(str(value) for value in payload.values() if value)

    @staticmethod
    def extract_skills(payload: dict[str, Any]) -> list[str]:
        raw = EmploymentAIService.normalize_text(payload).lower()
        known = ["python", "fastapi", "sql", "docker", "kubernetes", "english", "telegram", "react"]
        return sorted([skill for skill in known if skill in raw])

    @staticmethod
    def vectorize(payload: dict[str, Any]) -> list[float]:
        # Fallback deterministic pseudo-embedding until provider-specific embeddings are wired.
        digest = sha256(EmploymentAIService.normalize_text(payload).encode("utf-8")).digest()
        return [b / 255 for b in digest[:64]]

    @staticmethod
    def build_match_percent(match_score: float) -> int:
        return max(0, min(100, round(match_score * 100)))

    @staticmethod
    def build_confidence(match_score: float) -> MatchConfidence:
        if match_score >= 0.75:
            return MatchConfidence.HIGH
        if match_score >= 0.45:
            return MatchConfidence.MEDIUM
        return MatchConfidence.LOW

    @staticmethod
    async def generate_explanation(candidate: dict[str, Any], vacancy: dict[str, Any], match_score: float) -> dict[str, Any]:
        if not settings.EMPLOYMENT_AI_ENABLED or not settings.GEMINI_API_KEY:
            return {
                "reasoning": "fallback_explanation",
                "matched_skills": EmploymentAIService.extract_skills(candidate),
                "missing_skills": [],
                "language": "multi",
            }

        prompt = {
            "candidate": candidate,
            "vacancy": vacancy,
            "match_score": match_score,
            "format": {
                "reasoning": "string",
                "matched_skills": ["string"],
                "missing_skills": ["string"],
                "language": "ru|kk|en|multi",
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        params = {"key": settings.GEMINI_API_KEY}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    params=params,
                    json={"contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}]},
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            logger.warning("Employment Gemini explanation failed: %s", exc)
            return {
                "reasoning": "fallback_explanation",
                "matched_skills": EmploymentAIService.extract_skills(candidate),
                "missing_skills": [],
                "language": "multi",
            }

        parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
        text = parts[0].get("text") if parts else None
        if not text:
            return {"reasoning": "fallback_explanation", "matched_skills": [], "missing_skills": [], "language": "multi"}

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        return {"reasoning": text[:500], "matched_skills": [], "missing_skills": [], "language": "multi"}
