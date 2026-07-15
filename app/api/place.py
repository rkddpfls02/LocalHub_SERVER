from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
import logging
import time

from app.schemas.place import PlaceCategoryListResponse, PlaceSearchResponse
from app.services.place_service import list_places_by_category, search_places_page


router = APIRouter(prefix="/places", tags=["places"])
logger = logging.getLogger(__name__)


@router.get("/search", response_model=PlaceSearchResponse)
def read_places_by_keyword(keyword: str = Query(..., min_length=1, max_length=100), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)) -> PlaceSearchResponse:
    started = time.perf_counter()
    safe_keyword = " ".join(keyword.split())[:100]
    try:
        result = search_places_page(db, safe_keyword, page, page_size)
        message = "place_search.no_results" if not result["total"] else "place_search.completed"
        logger.info("%s keyword=%r page=%d page_size=%d total=%d returned=%d duration_ms=%.2f", message, safe_keyword, page, page_size, result["total"], len(result["items"]), (time.perf_counter() - started) * 1000)
        return PlaceSearchResponse(**result)
    except Exception:
        logger.exception("place_search.failed keyword=%r page=%d page_size=%d", safe_keyword, page, page_size)
        raise


@router.get("/category", response_model=PlaceCategoryListResponse)
def read_places_by_category(
    contentTypeId: int = Query(..., description="contentTypeId 값, 예: 12(관광지), 14(문화시설)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(4, ge=1, le=20),
    db: Session = Depends(get_db),
) -> PlaceCategoryListResponse:
    result = list_places_by_category(db, contentTypeId, page=page, page_size=page_size)
    return PlaceCategoryListResponse(**result)
