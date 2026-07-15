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
            addr1=festival.addr1 or "",
            startDate=festival.start_date.isoformat(),
            endDate=festival.end_date.isoformat(),
            eventstartdate=festival.eventstartdate or festival.start_date.strftime("%Y%m%d"),
            eventenddate=festival.eventenddate or festival.end_date.strftime("%Y%m%d"),
            eventplace=festival.eventplace,
            playtime=festival.playtime,
            program=festival.program,
            subevent=festival.subevent,
            sponsor1=festival.sponsor1,
            sponsor1tel=festival.sponsor1tel,
            sponsor2=festival.sponsor2,
            sponsor2tel=festival.sponsor2tel,
            eventhomepage=festival.eventhomepage,
            bookingplace=festival.bookingplace,
            agelimit=festival.agelimit,
            festivalgrade=festival.festivalgrade,
            placeinfo=festival.placeinfo,
            spendtimefestival=festival.spendtimefestival,
            discountinfofestival=festival.discountinfofestival,
            usetimefestival=festival.usetimefestival,
        )
        for festival in festivals
    ]
