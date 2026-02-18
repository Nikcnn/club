from apps.search.personalization import (
    BonusWeights,
    build_profile_vector,
    compute_user_preferences,
    rerank_results,
)


def test_rerank_role_boost() -> None:
    items = [
        {"type": "club", "score": 0.9, "city": None, "category": None},
        {"type": "campaign", "score": 0.9, "city": None, "category": None},
    ]

    reranked = rerank_results(
        items,
        user_role="investor",
        preferences={"top_cities": [], "top_categories": [], "top_types": [], "type_counts": {}},
        weights=BonusWeights(),
        role_boost=True,
    )

    assert reranked[0]["type"] == "campaign"


def test_compute_preferences_from_clicks() -> None:
    clicks = [
        {"city": "Almaty", "category": "IT", "doc_type": "campaign"},
        {"city": "Almaty", "category": "IT", "doc_type": "campaign"},
        {"city": "Astana", "category": "Sport", "doc_type": "club"},
    ]

    prefs = compute_user_preferences(clicks)

    assert prefs["top_cities"][0] == "Almaty"
    assert prefs["top_categories"][0] == "IT"
    assert prefs["top_types"][0] == "campaign"


def test_build_profile_vector_mean_pooling() -> None:
    vectors = [[1.0, 0.0], [0.0, 1.0]]
    pooled = build_profile_vector(vectors)

    assert round(pooled[0], 6) == round(0.70710678118, 6)
    assert round(pooled[1], 6) == round(0.70710678118, 6)
