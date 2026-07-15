from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.models.place import Place


def normalize_place_image_url(url: str | None) -> str | None:
    if not url:
        return url
    if url.startswith("http://tong.visitkorea.or.kr/"):
        return f"https://{url.removeprefix('http://')}"
    return url


def search_places(db: Session, keyword: str, limit: int = 20) -> list[dict]:
    normalized_keyword = (keyword or "").strip()
    if not normalized_keyword:
        return []

    tokens = [token for token in normalized_keyword.split() if token]
    if not tokens:
        return []

    query = db.query(Place)
    for token in tokens:
        token_filter = f"%{token}%"
        query = query.filter(
            or_(
                Place.title.ilike(token_filter),
                Place.addr1.ilike(token_filter),
            )
        )

    places = query.order_by(
        case(
            (Place.title == normalized_keyword, 0),
            else_=1,
        ),
        Place.title.asc(),
    ).limit(limit).all()
    return [
        {
            "id": place.id,
            "content_id": place.content_id,
            "title": place.title,
            "address": " ".join(part for part in (place.addr1, place.addr2) if part),
        }
        for place in places
    ]


def search_places_page(db: Session, keyword: str, page: int = 1, page_size: int = 20) -> dict:
    normalized_keyword = " ".join((keyword or "").split())
    if not normalized_keyword:
        return {
            "keyword": "",
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0,
            "items": [],
        }

    tokens = normalized_keyword.split()
    query = db.query(Place)
    for token in tokens:
        pattern = f"%{token}%"
        query = query.filter(
            or_(
                Place.title.ilike(pattern),
                Place.addr1.ilike(pattern),
                Place.addr2.ilike(pattern),
            )
        )

    exact = Place.title == normalized_keyword
    starts = Place.title.ilike(f"{normalized_keyword}%")
    total = query.count()
    places = (
        query.order_by(
            case(
                (exact, 0),
                (starts, 1),
                (Place.title.ilike(f"%{normalized_keyword}%"), 2),
                else_=3,
            ),
            Place.title.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "keyword": normalized_keyword,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
        "items": [
            {
                "id": place.id,
                "content_id": place.content_id,
                "title": place.title,
                "address": " ".join(part for part in (place.addr1, place.addr2) if part),
                "first_image": normalize_place_image_url(place.first_image),
                "contentTypeId": place.content_type_id,
                "category": place.content_type,
                "avg_rating": float(place.avg_rating or 0.0),
                "post_cnt": int(place.post_cnt or 0),
            }
            for place in places
        ],
    }


def list_places_by_category(db: Session, content_type_id: int, page: int = 1, page_size: int = 4) -> dict:
    if content_type_id is None:
        return {
            "contentTypeId": 0,
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0,
            "items": [],
        }

    query = db.query(Place).filter(Place.content_type_id == content_type_id)
    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total else 0

    offset = (page - 1) * page_size
    places = query.order_by(Place.title.asc()).offset(offset).limit(page_size).all()

    items = [
        {
            "id": place.id,
            "content_id": place.content_id,
            "title": place.title,
            "address": " ".join(part for part in (place.addr1, place.addr2) if part),
            "first_image": normalize_place_image_url(place.first_image),
            "contentTypeId": place.content_type_id,
            "category": place.content_type,
            "avg_rating": float(place.avg_rating or 0.0),
            "post_cnt": int(place.post_cnt or 0),
        }
        for place in places
    ]

    return {
        "contentTypeId": content_type_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "items": items,
    }
