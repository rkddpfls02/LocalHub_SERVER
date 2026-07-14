from pydantic import BaseModel


class PlaceSearchItem(BaseModel):
    id: int
    content_id: str
    title: str
    address: str


class PlaceByContentIdResponse(BaseModel):
    id: int
    content_id: str
    title: str
    region: str
    content_type: str
    content_type_id: int
    addr1: str | None
    addr2: str | None
    first_image: str | None
