import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.festival import Festival
from app.models.place import Place


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
FESTIVAL_DATA_FILE = DATA_DIR / "festival.json"


def _resolve_data_file(region: str, content_type: str) -> Path:
    filename = f"{region}_{content_type}.json"
    return DATA_DIR / filename


def _build_place_from_item(payload: dict[str, Any], item: dict[str, Any]) -> Place:
    content_type_id = payload.get("contentTypeId")
    return Place(
        content_id=str(item.get("contentid")),
        region=payload.get("region", ""),
        content_type=payload.get("contentType", ""),
        content_type_id=int(content_type_id) if content_type_id is not None else 0,
        title=item.get("title", ""),
        addr1=item.get("addr1", ""),
        addr2=item.get("addr2", ""),
        areacode=item.get("areacode", ""),
        cat1=item.get("cat1", ""),
        cat2=item.get("cat2", ""),
        cat3=item.get("cat3", ""),
        tel=item.get("tel", ""),
        zipcode=item.get("zipcode", ""),
        first_image=item.get("firstimage", ""),
        first_image2=item.get("firstimage2", ""),
        cpyrht_div_cd=item.get("cpyrhtDivCd", ""),
        mapx=item.get("mapx", ""),
        mapy=item.get("mapy", ""),
        mlevel=item.get("mlevel", ""),
        sigungucode=item.get("sigungucode", ""),
        l_dong_regn_cd=item.get("lDongRegnCd", ""),
        l_dong_signgu_cd=item.get("lDongSignguCd", ""),
        lcls_systm1=item.get("lclsSystm1", ""),
        lcls_systm2=item.get("lclsSystm2", ""),
        lcls_systm3=item.get("lclsSystm3", ""),
        created_time=item.get("createdtime", ""),
        modified_time=item.get("modifiedtime", ""),
        raw_data=json.dumps(item, ensure_ascii=False),
    )


def load_place_jsons(
    db: Session,
    region: str | None = None,
    content_type: str | None = None,
    content_type_id: int | None = None,
    overwrite: bool = False,
) -> int:
    if overwrite:
        db.query(Place).delete()
        db.commit()

    if region and content_type:
        file_path = _resolve_data_file(region, content_type)
        if not file_path.exists():
            return 0

        with file_path.open("r", encoding="utf-8") as f:
            payload: dict[str, Any] = json.load(f)

        created = 0
        for item in payload.get("items", []):
            if overwrite:
                db.add(_build_place_from_item(payload, item))
                created += 1
                continue

            existing = db.query(Place).filter(Place.content_id == str(item.get("contentid"))).first()
            if existing:
                continue

            db.add(_build_place_from_item(payload, item))
            created += 1

        db.commit()
        return created

    created = 0
    for file_path in sorted(DATA_DIR.glob("*.json")):
        if file_path == FESTIVAL_DATA_FILE:
            continue
        with file_path.open("r", encoding="utf-8") as f:
            payload: dict[str, Any] = json.load(f)

        for item in payload.get("items", []):
            if overwrite:
                db.add(_build_place_from_item(payload, item))
                created += 1
                continue

            existing = db.query(Place).filter(Place.content_id == str(item.get("contentid"))).first()
            if existing:
                continue

            db.add(_build_place_from_item(payload, item))
            created += 1

    db.commit()
    return created


def load_festival_json(db: Session, overwrite: bool = False) -> int:
    if not FESTIVAL_DATA_FILE.exists():
        return 0

    if overwrite:
        db.query(Festival).delete()
        db.commit()

    with FESTIVAL_DATA_FILE.open("r", encoding="utf-8") as file:
        payload: dict[str, Any] = json.load(file)

    created = 0
    for item in payload.get("items", []):
        try:
            start_date = date.fromisoformat(item["startDate"])
            end_date = date.fromisoformat(item["endDate"])
        except (KeyError, TypeError, ValueError):
            continue

        if not overwrite:
            existing = db.query(Festival).filter(
                Festival.title == item.get("title", ""),
                Festival.start_date == start_date,
                Festival.end_date == end_date,
            ).first()
            if existing:
                continue

        db.add(Festival(
            title=item.get("title", ""),
            start_date=start_date,
            end_date=end_date,
            addr1=item.get("addr1", ""),
        ))
        created += 1

    db.commit()
    return created
