from __future__ import annotations

import json

import pytest

from apps.employment.ai_service import EmploymentAIService


@pytest.mark.asyncio
async def test_generate_explanation_fallback_hybrid_skills(monkeypatch):
    monkeypatch.setattr("apps.employment.ai_service.settings.EMPLOYMENT_AI_ENABLED", False)
    monkeypatch.setattr("apps.employment.ai_service.settings.GEMINI_API_KEY", None)

    candidate = {"resume_text": "5 years Python, PostgreSQL and переговоры по продажам"}
    vacancy = {"position_title": "Backend"}

    result = await EmploymentAIService.generate_explanation(candidate, vacancy, 0.8)

    assert result["reasoning"] == "fallback_explanation"
    assert "python" in result["matched_skills"]
    assert "sql" in result["matched_skills"]
    assert "negotiation" in result["matched_skills"]
    assert "sales" in result["matched_skills"]


@pytest.mark.asyncio
async def test_generate_explanation_normalizes_llm_response(monkeypatch):
    monkeypatch.setattr("apps.employment.ai_service.settings.EMPLOYMENT_AI_ENABLED", True)
    monkeypatch.setattr("apps.employment.ai_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("apps.employment.ai_service.settings.GEMINI_MODEL", "gemini-test")

    response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "reasoning": "```json Based on the provided structure sample json response```",
                                    "matched_skills": ["PostgreSQL", "python"],
                                    "missing_skills": ["Kubernetes"],
                                    "language": "RU",
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }

    captured_request = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return response_payload

    class DummyClient:
        def __init__(self, *args, **kwargs):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, params=None, json=None):
            captured_request["url"] = url
            captured_request["params"] = params
            captured_request["json"] = json
            return DummyResponse()

    monkeypatch.setattr("apps.employment.ai_service.httpx.AsyncClient", DummyClient)

    candidate = {"resume_text": "Python developer with PostgreSQL"}
    vacancy = {"position_title": "Senior Backend", "skills": "Kubernetes"}
    result = await EmploymentAIService.generate_explanation(candidate, vacancy, 0.9)

    assert captured_request["json"]["system_instruction"]["parts"][0]["text"].startswith("You are an employment matching assistant")
    assert captured_request["json"]["generationConfig"]["response_mime_type"] == "application/json"

    assert result["language"] == "ru"
    assert "python" in result["matched_skills"]
    assert "sql" in result["matched_skills"]
    assert "kubernetes" in result["missing_skills"]
    assert "```" not in result["reasoning"]
