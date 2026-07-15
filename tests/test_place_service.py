from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.place import Place
from app.services.place_service import list_places_by_category, normalize_place_image_url, search_places


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


def test_list_places_by_category_includes_first_image():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    place = make_place(1, "Image Place")
    place.first_image = "http://tong.visitkorea.or.kr/cms/place.jpg"
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
    }]


def test_normalize_place_image_url_preserves_other_urls_and_empty_values():
    assert normalize_place_image_url("https://tong.visitkorea.or.kr/cms/place.jpg") == "https://tong.visitkorea.or.kr/cms/place.jpg"
    assert normalize_place_image_url("http://example.com/place.jpg") == "http://example.com/place.jpg"
    assert normalize_place_image_url(None) is None
