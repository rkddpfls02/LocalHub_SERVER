from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.models.festival import Festival
from app.schemas.festival import FestivalItem


def list_festivals(db: Session, year: int, month: int) -> list[FestivalItem]:
    month_start = date(year, month, 1)
    month_end = date(year, month, monthrange(year, month)[1])

    festivals = db.query(Festival).filter(
        Festival.start_date <= month_end,
        Festival.end_date >= month_start,
    ).order_by(Festival.start_date.asc(), Festival.title.asc()).all()

    return [
        FestivalItem(
            title=festival.title,
            startDate=festival.start_date.isoformat(),
            endDate=festival.end_date.isoformat(),
            addr1=festival.addr1,
        )
        for festival in festivals
    ]
