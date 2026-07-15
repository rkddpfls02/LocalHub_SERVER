from pydantic import BaseModel


class FestivalItem(BaseModel):
    title: str
    addr1: str = ""
    startDate: str
    endDate: str
    eventstartdate: str | None = None
    eventenddate: str | None = None
    eventplace: str | None = None
    playtime: str | None = None
    program: str | None = None
    subevent: str | None = None
    sponsor1: str | None = None
    sponsor1tel: str | None = None
    sponsor2: str | None = None
    sponsor2tel: str | None = None
    eventhomepage: str | None = None
    bookingplace: str | None = None
    agelimit: str | None = None
    festivalgrade: str | None = None
    placeinfo: str | None = None
    spendtimefestival: str | None = None
    discountinfofestival: str | None = None
    usetimefestival: str | None = None


class FestivalListResponse(BaseModel):
    year: int
    month: int
    total: int
    items: list[FestivalItem]
