from __future__ import annotations

import json
import logging
import re
from hashlib import sha512
from typing import Any
from google.genai import types
import httpx
from google import genai



def _build_genai_client() -> genai.Client:
    return genai.Client(api_key=settings.GEMINI_API_KEY)
from apps.core.settings import settings
from apps.employment.enums import MatchConfidence

logger = logging.getLogger(__name__)


class EmploymentAIService:
    KNOWN_SKILLS = {
        "python", "fastapi", "sql", "docker", "kubernetes", "english", "telegram",
        "react", "sales", "negotiation", "excel", "accounting", "crm",
        "communication", "management",
    }

    SKILL_SYNONYMS = {
        "postgres": "sql",
        "postgresql": "sql",
        "1c": "accounting",
        "amo crm": "crm",
        "bitrix24": "crm",
        "переговор": "negotiation",
        "продаж": "sales",
    }

    RESPONSE_LANGUAGES = {"ru", "kk", "en", "multi"}

    @staticmethod
    def normalize_text(payload: dict[str, Any]) -> str:
        return " ".join(str(value) for value in payload.values() if value)

    @staticmethod
    def extract_skills(payload: dict[str, Any], llm_skills: list[str] | None = None) -> list[str]:
        raw = EmploymentAIService.normalize_text(payload).lower()
        normalized_raw = re.sub(r"\s+", " ", raw)

        lexical_skills = {skill for skill in EmploymentAIService.KNOWN_SKILLS if skill in normalized_raw}
        for synonym, normalized in EmploymentAIService.SKILL_SYNONYMS.items():
            if synonym in normalized_raw:
                lexical_skills.add(normalized)

        llm_normalized: set[str] = set()
        for skill in llm_skills or []:
            s = str(skill).strip().lower()
            if not s:
                continue
            llm_normalized.add(EmploymentAIService.SKILL_SYNONYMS.get(s, s))

        return sorted(lexical_skills | llm_normalized)

    @staticmethod
    def vectorize(payload: dict[str, Any]) -> list[float]:
        digest = sha512(EmploymentAIService.normalize_text(payload).encode("utf-8")).digest()
        return [b / 255 for b in digest]  # 64 значения

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
    async def generate_explanation(candidate: dict[str, Any], vacancy: dict[str, Any], match_score: float) -> dict[
        str, Any]:
        fallback_skills = EmploymentAIService.extract_skills(candidate)

        if not settings.EMPLOYMENT_AI_ENABLED or not settings.GEMINI_API_KEY:
            return {
                "reasoning": "fallback_explanation",
                "matched_skills": fallback_skills,
                "missing_skills": [],
                "language": "multi",
            }

        prompt = {
            "candidate": candidate,
            "vacancy": vacancy,
            "match_score": match_score,
        }

        system_text = (
            "You are an employment matching assistant. "
            "Return strictly valid JSON object with keys: reasoning, matched_skills, missing_skills, language. "
            "Do not include markdown, code fences, extra commentary or examples. "
            "language must be one of: ru, kk, en, multi."
        )

        client = _build_genai_client()

        try:
            resp = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,  # например "gemini-3-flash-preview"
                contents=json.dumps(prompt, ensure_ascii=False),
                config=types.GenerateContentConfig(
                    system_instruction=[system_text],
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            text = resp.text
        except Exception as exc:
            logger.warning("Employment Gemini explanation failed: %s", exc)
            return {
                "reasoning": "fallback_explanation",
                "matched_skills": fallback_skills,
                "missing_skills": [],
                "language": "multi",
            }

        if not text:
            return {
                "reasoning": "fallback_explanation",
                "matched_skills": fallback_skills,
                "missing_skills": [],
                "language": "multi",
            }

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return EmploymentAIService._normalize_explanation(parsed, candidate, vacancy, match_score)
        except json.JSONDecodeError:
            pass

        return EmploymentAIService._normalize_explanation({"reasoning": text}, candidate, vacancy, match_score)
    @staticmethod
    def _sanitize_reasoning(text: str) -> str:
        cleaned = str(text).strip()
        cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("```", "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:500] or "fallback_explanation"

    @staticmethod
    def _as_skill_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _normalize_explanation(
        raw: dict[str, Any],
        candidate: dict[str, Any],
        vacancy: dict[str, Any],
        match_score: float,
    ) -> dict[str, Any]:
        matched_llm = EmploymentAIService._as_skill_list(raw.get("matched_skills"))
        missing_llm = EmploymentAIService._as_skill_list(raw.get("missing_skills"))

        candidate_skills = EmploymentAIService.extract_skills(candidate, llm_skills=matched_llm)
        vacancy_skills = EmploymentAIService.extract_skills(vacancy)

        # если LLM не дал missing_skills — считаем разницу вакансия - кандидат
        if missing_llm:
            missing = EmploymentAIService.extract_skills({"skills": " ".join(missing_llm)})
        else:
            missing = sorted(set(vacancy_skills) - set(candidate_skills))

        language = str(raw.get("language", "multi")).lower().strip()
        if language not in EmploymentAIService.RESPONSE_LANGUAGES:
            language = "multi"

        reasoning = EmploymentAIService._sanitize_reasoning(raw.get("reasoning", ""))

        if reasoning == "fallback_explanation" and match_score >= 0.8 and candidate_skills:
            reasoning = f"Strong match based on overlapping skills: {', '.join(candidate_skills[:5])}."

        return {
            "reasoning": reasoning,
            "matched_skills": candidate_skills,
            "missing_skills": missing,
            "language": language,
        }