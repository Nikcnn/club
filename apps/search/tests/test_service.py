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


def test_city_query_precision_filter_prefers_exact_phrase_in_title_or_snippet() -> None:
    items = [
        {
            "type": "club",
            "title": "Молочные коты",
            "snippet": "Клуб по интересам",
        },
        {
            "type": "club",
            "title": "Молочные твари",
            "snippet": "Точное название",
        },
    ]

    filtered = SearchService._city_query_precision_filter(items=items, q="молочные твари", city="Astana")

    assert len(filtered) == 1
    assert filtered[0]["title"] == "Молочные твари"


def test_city_query_precision_filter_returns_empty_for_partial_word_overlap() -> None:
    items = [
        {
            "type": "club",
            "title": "Молочные коты",
            "snippet": "Описание про котов",
        },
        {
            "type": "club",
            "title": "Твари ночи",
            "snippet": "Описание про другое",
        },
    ]

    filtered = SearchService._city_query_precision_filter(items=items, q="молочные твари", city="Astana")

    assert filtered == []


def test_city_query_precision_filter_returns_nearest_number_when_exact_missing() -> None:
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

    filtered = SearchService._city_query_precision_filter(items=items, q="222", city="Astana")

    assert len(filtered) == 1
    assert filtered[0]["title"] == "Club 221"


def test_city_query_precision_filter_keeps_items_without_city_constraint() -> None:
    items = [
        {
            "type": "club",
            "title": "Chess Club",
            "snippet": "Astana chess",
        }
    ]

    filtered = SearchService._city_query_precision_filter(items=items, q="chess", city=None)

    assert filtered == items
