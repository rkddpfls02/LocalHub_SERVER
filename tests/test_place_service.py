from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.place import Place
from app.services.place_service import (
    list_places_by_category,
    normalize_place_image_url,
    search_places,
    search_places_page,
)


def make_place(index: int, title: str) -> Place:
    return Place(
        content_id=f"content-{index}",
        region="Busan",
        content_type="place",
        content_type_id=12,
        title=title,
        addr1="Busan",
    )


def test_search_places_prioritizes_all_exact_title_matches_before_partial_matches():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    keyword = "Search Target"

    partial_matches = [make_place(index, f"A {keyword} {index:02d}") for index in range(1, 22)]
    exact_matches = [
        make_place(100, keyword),
        make_place(101, keyword),
    ]
    session.add_all(partial_matches + exact_matches)
    session.commit()

    results = search_places(session, keyword)

    assert len(results) == 20
    assert [result["title"] for result in results[:2]] == [keyword, keyword]
    assert {result["content_id"] for result in results[:2]} == {"content-100", "content-101"}
    assert all(set(result) == {"id", "content_id", "title", "address"} for result in results)


def test_search_places_page_searches_all_card_fields_and_paginates():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    exact_match = make_place(1, "Search Target")
    exact_match.first_image = "http://tong.visitkorea.or.kr/cms/search.jpg"
    exact_match.avg_rating = 4.5
    exact_match.post_cnt = 7
    partial_title = make_place(2, "A Search Target")
    address_one = make_place(3, "Address One")
    address_one.addr1 = "Search Target district"
    address_two = make_place(4, "Address Two")
    address_two.addr2 = "Search Target building"
    session.add_all([exact_match, partial_title, address_one, address_two])
    session.commit()

    result = search_places_page(session, "Search Target", page=1, page_size=2)

    assert result["total"] == 4
    assert result["total_pages"] == 2
    assert result["page"] == 1
    assert [item["title"] for item in result["items"]] == ["Search Target", "A Search Target"]
    assert result["items"][0]["first_image"] == "https://tong.visitkorea.or.kr/cms/search.jpg"
    assert result["items"][0]["avg_rating"] == 4.5
    assert result["items"][0]["post_cnt"] == 7

    second_page = search_places_page(session, "Search Target", page=2, page_size=2)
    assert [item["title"] for item in second_page["items"]] == ["Address One", "Address Two"]


def test_list_places_by_category_includes_first_image_and_review_stats():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    place = make_place(1, "Image Place")
    place.first_image = "http://tong.visitkorea.or.kr/cms/place.jpg"
    place.avg_rating = 4.25
    place.post_cnt = 3
    session.add(place)
    session.commit()

    result = list_places_by_category(session, 12)

    assert result["page_size"] == 4
    assert result["items"] == [{
        "id": place.id,
        "content_id": "content-1",
        "title": "Image Place",
        "address": "Busan",
        "first_image": "https://tong.visitkorea.or.kr/cms/place.jpg",
        "contentTypeId": 12,
        "category": "place",
        "avg_rating": 4.25,
        "post_cnt": 3,
    }]


def test_list_places_by_category_uses_safe_default_review_stats():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    place = make_place(1, "No Reviews")
    place.avg_rating = None
    place.post_cnt = None
    session.add(place)
    session.commit()

    result = list_places_by_category(session, 12)

    assert result["items"][0]["avg_rating"] == 0.0
    assert result["items"][0]["post_cnt"] == 0
    assert result["page"] == 1
    assert result["page_size"] == 4


def test_normalize_place_image_url_preserves_other_urls_and_empty_values():
    assert normalize_place_image_url("https://tong.visitkorea.or.kr/cms/place.jpg") == "https://tong.visitkorea.or.kr/cms/place.jpg"
    assert normalize_place_image_url("http://example.com/place.jpg") == "http://example.com/place.jpg"
    assert normalize_place_image_url(None) is None
