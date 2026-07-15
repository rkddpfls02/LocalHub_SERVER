from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.route import RouteOptimizeRequest, RouteOptimizeResponse
from app.services.route_service import optimize_route

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.post("/optimize", response_model=RouteOptimizeResponse)
def optimize_route_endpoint(
    payload: RouteOptimizeRequest | None = None,
    db: Session = Depends(get_db),
) -> RouteOptimizeResponse:
    result = optimize_route(
        db=db,
        start_place=None,
        places=None,
    )
    return RouteOptimizeResponse(**result)
