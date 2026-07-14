from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.place import Place


def get_place_by_content_id(db: Session, content_id: str) -> Place:
    place = db.query(Place).filter(Place.content_id == content_id).first()
    if place is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장소를 찾을 수 없습니다.",
        )
    return place


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

    places = query.order_by(Place.title.asc()).limit(limit).all()
    return [
        {
            "id": place.id,
            "content_id": place.content_id,
            "title": place.title,
            "address": " ".join(part for part in (place.addr1, place.addr2) if part),
        }
        for place in places
    ]
