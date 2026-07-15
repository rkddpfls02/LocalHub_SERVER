import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.festival import Festival
from app.services.festival_service import list_festivals
from app.utils import load_json_data


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_festival_response_includes_normalized_image_fields():
    session = make_session()
    session.add(Festival(
        title="Image Festival",
        start_date=date(2026, 8, 6),
        end_date=date(2026, 8, 9),
        content_id="festival-1",
        first_image="http://tong.visitkorea.or.kr/cms/festival.jpg",
    ))
    session.commit()

    item = list_festivals(session, 2026, 8)[0]

    assert item.contentId == "festival-1"
    assert item.firstImage == "https://tong.visitkorea.or.kr/cms/festival.jpg"
    assert item.firstImage2 is None
    assert item.eventplace is None


def test_backfill_festival_images_fills_only_missing_values(tmp_path, monkeypatch):
    source = tmp_path / "festival.json"
    source.write_text(json.dumps({"items": [{
        "title": "Backfill Festival",
        "contentid": "festival-2",
        "eventstartdate": "20260806",
        "eventenddate": "20260809",
        "firstimage": "http://tong.visitkorea.or.kr/cms/first.jpg",
        "firstimage2": "https://tong.visitkorea.or.kr/cms/second.jpg",
    }]}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(load_json_data, "FESTIVAL_DATA_FILE", source)
    session = make_session()
    festival = Festival(
        title="Backfill Festival",
        start_date=date(2026, 8, 6),
        end_date=date(2026, 8, 9),
        first_image="https://existing.example/image.jpg",
    )
    session.add(festival)
    session.commit()

    assert load_json_data.backfill_festival_images(session) == 1
    assert load_json_data.backfill_festival_images(session) == 0
    session.refresh(festival)
    assert festival.content_id == "festival-2"
    assert festival.first_image == "https://existing.example/image.jpg"
    assert festival.first_image2 == "https://tong.visitkorea.or.kr/cms/second.jpg"
