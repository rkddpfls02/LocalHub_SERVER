import json
from calendar import monthrange
from datetime import date
from pathlib import Path

from app.schemas.festival import FestivalItem


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FESTIVAL_DATA_FILE = PROJECT_ROOT / "data" / "festival.json"


def list_festivals(year: int, month: int) -> list[FestivalItem]:
    month_start = date(year, month, 1)
    month_end = date(year, month, monthrange(year, month)[1])

    with FESTIVAL_DATA_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    festivals = []
    for item in payload.get("items", []):
        try:
            start_date = date.fromisoformat(item["startDate"])
            end_date = date.fromisoformat(item["endDate"])
        except (KeyError, TypeError, ValueError):
            continue

        if start_date <= month_end and end_date >= month_start:
            festivals.append(FestivalItem(
                title=item.get("title", ""),
                startDate=item["startDate"],
                endDate=item["endDate"],
                addr1=item.get("addr1", ""),
            ))

    return sorted(festivals, key=lambda festival: (festival.startDate, festival.title))
