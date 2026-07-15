from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.festival import FestivalListResponse
from app.services.festival_service import list_festivals


router = APIRouter(prefix="/festivals", tags=["festivals"])


@router.get("", response_model=FestivalListResponse)
def read_festivals(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
) -> FestivalListResponse:
    items = list_festivals(db, year, month)
    return FestivalListResponse(
        year=year,
        month=month,
        total=len(items),
        items=items,
    )
