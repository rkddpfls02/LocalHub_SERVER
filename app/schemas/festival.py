from pydantic import BaseModel


class FestivalItem(BaseModel):
    title: str
    startDate: str
    endDate: str
    addr1: str


class FestivalListResponse(BaseModel):
    year: int
    month: int
    total: int
    items: list[FestivalItem]
