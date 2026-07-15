import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.place import Place

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)

logger = logging.getLogger(__name__)

TMAP_API_URL = "https://apis.openapi.sk.com/tmap/routes/routeSequential30"
TMAP_APP_KEY = os.getenv("TMAP_APP_KEY", "")
REQUIRED_CONTENT_TYPE_IDS = [12, 14, 28, 38, 32]


def build_tmap_request_payload(start_place: dict[str, Any], places: list[dict[str, Any]]) -> dict[str, Any]:
    end_place = places[-1] if places else start_place
    return {
        "version": 1,
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "startName": start_place.get("name") or "start",
        "startX": str(start_place.get("longitude") or ""),
        "startY": str(start_place.get("latitude") or ""),
        "startTime": datetime.now().strftime("%Y%m%d%H%M"),
        "endName": end_place.get("name") or "end",
        "endX": str(end_place.get("longitude") or start_place.get("longitude") or ""),
        "endY": str(end_place.get("latitude") or start_place.get("latitude") or ""),
        "searchOption": 0,
        "carType": 1,
        "viaPoints": [
            {
                "viaPointId": str(place.get("placeId") or place.get("id") or idx),
                "viaPointName": place.get("name") or f"place_{idx + 1}",
                "viaX": str(place.get("longitude") or ""),
                "viaY": str(place.get("latitude") or ""),
            }
            for idx, place in enumerate(places)
        ],
    }


def select_random_places(db: Session) -> list[dict[str, Any]]:
    selected_places: list[dict[str, Any]] = []
    for content_type_id in REQUIRED_CONTENT_TYPE_IDS:
        candidates = (
            db.query(Place)
            .filter(Place.content_type_id == content_type_id)
            .order_by(Place.id.asc())
            .all()
        )
        if not candidates:
            continue

        random_place = random.choice(candidates)
        selected_places.append(
            {
                "placeId": random_place.id,
                "name": random_place.title,
                "latitude": float(random_place.mapy) if random_place.mapy else 0.0,
                "longitude": float(random_place.mapx) if random_place.mapx else 0.0,
                "contentTypeId": random_place.content_type_id,
                "contentType": random_place.content_type,
                "address": " ".join(part for part in (random_place.addr1, random_place.addr2) if part),
                "firstImage": random_place.first_image,
            }
        )
    return selected_places


def optimize_route(db: Session | None, start_place: dict[str, Any] | None = None, places: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not places:
        if db is None:
            raise HTTPException(status_code=400, detail="DB가 필요합니다.")
        places = select_random_places(db)

    if not places:
        raise HTTPException(status_code=400, detail="선택 가능한 장소가 없습니다.")

    if len(places) != len(REQUIRED_CONTENT_TYPE_IDS):
        raise HTTPException(status_code=400, detail="경로 생성에 필요한 5개 카테고리의 장소가 모두 필요합니다.")

    if not start_place:
        start_place = random.choice(places)

    via_places = [place for place in places if place is not start_place]

    if not TMAP_APP_KEY:
        logger.error("TMAP_APP_KEY is missing. Check .env loading for the current process.")
        raise HTTPException(status_code=500, detail="TMAP_APP_KEY 환경변수가 설정되지 않았습니다.")

    payload = build_tmap_request_payload(start_place, via_places)
    try:
        response = requests.post(
            TMAP_API_URL,
            params={"version": 1},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "appKey": TMAP_APP_KEY,
            },
            json=payload,
            timeout=10,
        )
    except requests.Timeout as exc:
        logger.exception("Tmap API timeout", exc_info=exc)
        raise HTTPException(status_code=503, detail="Tmap API 요청 시간이 초과되었습니다.") from None
    except requests.RequestException as exc:
        logger.exception("Tmap API request failed", exc_info=exc)
        raise HTTPException(status_code=503, detail=f"Tmap API 요청 실패: {exc}") from exc

    if response.status_code == 401:
        logger.error("Tmap API authentication failed: %s", response.text)
        raise HTTPException(status_code=401, detail="Tmap API 인증에 실패했습니다.")
    if response.status_code >= 400:
        logger.error("Tmap API call failed: %s %s", response.status_code, response.text)
        raise HTTPException(status_code=502, detail="Tmap API 호출에 실패했습니다.")

    try:
        data = response.json()
    except ValueError as exc:
        logger.exception("Tmap API invalid response", exc_info=exc)
        raise HTTPException(status_code=502, detail="Tmap API 응답이 올바르지 않습니다.") from exc

    features = data.get("features") or []
    total_distance = data.get("totalDistance") or 0
    total_time = data.get("totalTime") or 0

    optimized_via_places = []
    if via_places:
        places_by_id = {
            str(place.get("placeId") or place.get("id")): place
            for place in via_places
        }
        optimized_via_places = [
            places_by_id[str(point.get("viaPointId"))]
            for point in (data.get("viaPoints") or [])
            if str(point.get("viaPointId")) in places_by_id
        ]
        if len(optimized_via_places) != len(via_places):
            optimized_via_places = via_places

    ordered_places = [start_place] + optimized_via_places

    return {
        "totalDistance": total_distance,
        "totalTime": total_time,
        "places": [
            {
                "order": index,
                "placeId": place.get("placeId") or place.get("id"),
                "name": place.get("name"),
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
                "contentTypeId": place.get("contentTypeId"),
                "contentType": place.get("contentType"),
                "address": place.get("address"),
                "firstImage": place.get("firstImage"),
            }
            for index, place in enumerate(ordered_places, start=1)
        ],
        "routeGeoJson": {
            "type": "FeatureCollection",
            "features": features,
        },
    }
