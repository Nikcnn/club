from apps.search.service import SearchService


def test_build_doc_id() -> None:
    assert SearchService.build_doc_id("club", 123) == "club:123"


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
