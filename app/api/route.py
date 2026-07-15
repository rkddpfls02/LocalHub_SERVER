from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.route import RouteOptimizeResponse
from app.services.route_service import optimize_route


router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.post("/random", response_model=RouteOptimizeResponse)
def random_route(db: Session = Depends(get_db)) -> RouteOptimizeResponse:
    return RouteOptimizeResponse(**optimize_route(db))
