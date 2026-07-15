from pydantic import BaseModel


class RoutePlaceResponse(BaseModel):
    order: int
    placeId: int
    name: str
    latitude: float
    longitude: float
    contentTypeId: int | None = None
    contentType: str | None = None
    address: str | None = None
    firstImage: str | None = None


class RouteOptimizeResponse(BaseModel):
    totalDistance: int
    totalTime: int
    places: list[RoutePlaceResponse]
    routeGeoJson: dict
