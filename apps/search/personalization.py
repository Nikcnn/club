from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass
class BonusWeights:
    role_boost_weight: float = 0.05
    pref_city_weight: float = 0.02
    pref_category_weight: float = 0.02
    pref_type_weight: float = 0.02


def compute_user_preferences(click_payloads: list[dict[str, Any]], top_n: int = 3) -> dict[str, Any]:
    city_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()

    for click in click_payloads:
        city = click.get("city")
        category = click.get("category")
        doc_type = click.get("type") or click.get("doc_type")

        if city:
            city_counter[city] += 1
        if category:
            category_counter[category] += 1
        if doc_type:
            type_counter[doc_type] += 1

    return {
        "top_cities": [item for item, _ in city_counter.most_common(top_n)],
        "top_categories": [item for item, _ in category_counter.most_common(top_n)],
        "top_types": [item for item, _ in type_counter.most_common(top_n)],
        "type_counts": dict(type_counter),
    }


def build_profile_vector(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []

    size = len(vectors[0])
    means = [0.0] * size
    for vector in vectors:
        for idx in range(size):
            means[idx] += float(vector[idx])

    count = float(len(vectors))
    means = [value / count for value in means]

    norm = sqrt(sum(value * value for value in means))
    if norm == 0:
        return means

    return [value / norm for value in means]


def rerank_results(
    items: list[dict[str, Any]],
    user_role: str | None,
    preferences: dict[str, Any],
    weights: BonusWeights,
    role_boost: bool = True,
) -> list[dict[str, Any]]:
    top_cities = set(preferences.get("top_cities", []))
    top_categories = set(preferences.get("top_categories", []))
    top_types = set(preferences.get("top_types", []))
    type_counts: dict[str, int] = preferences.get("type_counts", {})

    for item in items:
        adjusted_score = float(item.get("score", 0.0))
        doc_type = item.get("type")

        if role_boost and user_role:
            if user_role == "investor" and doc_type == "campaign":
                adjusted_score += weights.role_boost_weight
            elif user_role == "member" and doc_type in {"club", "news"}:
                adjusted_score += weights.role_boost_weight
            elif user_role in {"club", "organization"} and doc_type in {"club", "news"}:
                adjusted_score += weights.role_boost_weight / 2

        if item.get("city") in top_cities:
            adjusted_score += weights.pref_city_weight
        if item.get("category") in top_categories:
            adjusted_score += weights.pref_category_weight
        if doc_type in top_types:
            adjusted_score += weights.pref_type_weight

        click_bias = type_counts.get(doc_type or "", 0)
        adjusted_score += min(click_bias * 0.005, 0.03)

        item["score"] = adjusted_score

    return sorted(items, key=lambda payload: payload.get("score", 0.0), reverse=True)
