from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.place import PlaceByContentIdResponse
from app.services.place_service import get_place_by_content_id


router = APIRouter(prefix="/places", tags=["places"])


@router.get("/by-content-id/{content_id}", response_model=PlaceByContentIdResponse)
def read_by_content_id(content_id: str, db: Session = Depends(get_db)):
    place = get_place_by_content_id(db, content_id)
    return PlaceByContentIdResponse(
        id=place.id,
        content_id=place.content_id,
        title=place.title,
        region=place.region,
        content_type=place.content_type,
        content_type_id=place.content_type_id,
        addr1=place.addr1,
        addr2=place.addr2,
        first_image=place.first_image,
    )
