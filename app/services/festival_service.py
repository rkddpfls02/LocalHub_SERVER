from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.models.festival import Festival
from app.schemas.festival import FestivalItem


def normalize_festival_image_url(url: str | None) -> str | None:
    if not url:
        return None
    normalized_url = url.strip()
    if not normalized_url:
        return None
    if normalized_url.startswith("http://tong.visitkorea.or.kr/"):
        return f"https://{normalized_url.removeprefix('http://')}"
    return normalized_url


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
            contentId=festival.content_id or None,
            firstImage=normalize_festival_image_url(festival.first_image),
            firstImage2=normalize_festival_image_url(festival.first_image2),
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
