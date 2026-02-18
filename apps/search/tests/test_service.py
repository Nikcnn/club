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


def test_strict_city_query_filter_removes_wrong_number_matches() -> None:
    items = [
        {
            "type": "club",
            "title": "Club 21",
            "snippet": "Mock club 21",
        },
        {
            "type": "club",
            "title": "Club 22",
            "snippet": "Mock club 22",
        },
    ]

    filtered = SearchService._strict_city_query_filter(items=items, q="22", city="Astana")

    assert len(filtered) == 1
    assert filtered[0]["title"] == "Club 22"


def test_strict_city_query_filter_keeps_results_when_query_has_no_numbers() -> None:
    items = [
        {
            "type": "club",
            "title": "Chess Club",
            "snippet": "Astana chess",
        }
    ]

    filtered = SearchService._strict_city_query_filter(items=items, q="chess", city="Astana")

    assert filtered == items
