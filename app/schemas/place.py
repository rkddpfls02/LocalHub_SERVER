from pydantic import BaseModel


class PlaceSearchItem(BaseModel):
    id: int
    content_id: str
    title: str
    address: str


class PlaceCategoryItem(BaseModel):
    id: int
    content_id: str
    title: str
    address: str
    first_image: str | None = None
    contentTypeId: int
    category: str


class PlaceCategoryListResponse(BaseModel):
    contentTypeId: int
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[PlaceCategoryItem]
