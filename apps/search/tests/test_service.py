import uuid

from apps.search.service import SearchService


def test_build_doc_id_is_stable_uuid5() -> None:
    expected = str(uuid.uuid5(uuid.NAMESPACE_DNS, "club:123"))
    assert SearchService.build_doc_id("club", 123) == expected


def test_build_text_skips_none() -> None:
    payload = {
        "title": "AI Club",
        "snippet": None,
        "city": "Almaty",
        "category": None,
        "status": "active",
    }

    text = SearchService.build_text(payload)

    assert "None" not in text
    assert text == "AI Club Almaty active"


def test_city_numeric_query_filter_prefers_exact_number_match() -> None:
    items = [
        {
            "type": "club",
            "title": "Club 221",
            "snippet": "Mock club 221",
        },
        {
            "type": "club",
            "title": "Club 222",
            "snippet": "Mock club 222",
        },
    ]

    filtered = SearchService._city_numeric_query_filter(items=items, q="222", city="Astana")

    assert len(filtered) == 1
    assert filtered[0]["title"] == "Club 222"


def test_city_numeric_query_filter_returns_nearest_when_exact_missing() -> None:
    items = [
        {
            "type": "club",
            "title": "Club 221",
            "snippet": "Mock club 221",
        },
        {
            "type": "club",
            "title": "Club 230",
            "snippet": "Mock club 230",
        },
    ]

    filtered = SearchService._city_numeric_query_filter(items=items, q="222", city="Astana")

    assert len(filtered) == 1
    assert filtered[0]["title"] == "Club 221"


def test_city_numeric_query_filter_keeps_results_when_query_has_no_numbers() -> None:
    items = [
        {
            "type": "club",
            "title": "Chess Club",
            "snippet": "Astana chess",
        }
    ]

    filtered = SearchService._city_numeric_query_filter(items=items, q="chess", city="Astana")

    assert filtered == items
