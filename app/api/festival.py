from fastapi import APIRouter, Query

from app.schemas.festival import FestivalListResponse
from app.services.festival_service import list_festivals


router = APIRouter(prefix="/festivals", tags=["festivals"])


@router.get("", response_model=FestivalListResponse)
def read_festivals(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> FestivalListResponse:
    items = list_festivals(year, month)
    return FestivalListResponse(
        year=year,
        month=month,
        total=len(items),
        items=items,
    )
