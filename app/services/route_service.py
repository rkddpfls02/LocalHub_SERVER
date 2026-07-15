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
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)

logger = logging.getLogger(__name__)

TMAP_API_URL = "https://apis.openapi.sk.com/tmap/routes/routeOptimization10"
TMAP_APP_KEY = os.getenv("TMAP_APP_KEY", "")
REQUIRED_CONTENT_TYPE_IDS = [12, 14, 28, 38, 32]


def build_tmap_request_payload(
    start_place: dict[str, Any],
    end_place: dict[str, Any],
    via_places: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "startName": start_place.get("name") or "start",
        "startX": str(start_place.get("longitude") or ""),
        "startY": str(start_place.get("latitude") or ""),
        "endName": end_place.get("name") or "end",
        "endX": str(end_place.get("longitude") or ""),
        "endY": str(end_place.get("latitude") or ""),
        "startTime": datetime.now().strftime("%Y%m%d%H%M"),
        "searchOption": "0",
        "viaPoints": [
            {
                "viaPointId": str(place.get("placeId") or place.get("id") or index),
                "viaPointName": place.get("name") or f"place_{index + 1}",
                "viaX": str(place.get("longitude") or ""),
                "viaY": str(place.get("latitude") or ""),
            }
            for index, place in enumerate(via_places, start=1)
        ],
    }


def select_random_places(db: Session) -> list[dict[str, Any]]:
    selected_places: list[dict[str, Any]] = []
    for content_type_id in REQUIRED_CONTENT_TYPE_IDS:
        candidates = db.query(Place).filter(Place.content_type_id == content_type_id).all()
        if not candidates:
            raise HTTPException(
                status_code=400,
                detail=f"contentTypeId={content_type_id} 장소가 없어 경로를 만들 수 없습니다.",
            )

        place = random.choice(candidates)
        selected_places.append(
            {
                "placeId": place.id,
                "name": place.title,
                "latitude": float(place.mapy) if place.mapy else 0.0,
                "longitude": float(place.mapx) if place.mapx else 0.0,
                "contentTypeId": place.content_type_id,
                "contentType": place.content_type,
                "address": " ".join(part for part in (place.addr1, place.addr2) if part),
                "firstImage": place.first_image,
            }
        )
    return selected_places


def _sum_feature_metric(features: list[dict[str, Any]], metric: str) -> int:
    total = 0
    for feature in features:
        properties = feature.get("properties") or {}
        try:
            total += int(properties.get(metric, 0))
        except (TypeError, ValueError):
            logger.warning("Ignoring invalid TMAP %s value: %r", metric, properties.get(metric))
    return total


def optimize_route(db: Session) -> dict[str, Any]:
    places = select_random_places(db)
    start_place = places[0]
    end_place = places[-1]
    via_places = places[1:-1]

    if not TMAP_APP_KEY:
        logger.error("TMAP_APP_KEY is missing. Check .env loading for the current process.")
        raise HTTPException(status_code=500, detail="TMAP_APP_KEY 환경변수가 설정되지 않았습니다.")

    try:
        response = requests.post(
            TMAP_API_URL,
            params={"version": 1},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "appKey": TMAP_APP_KEY,
            },
            json=build_tmap_request_payload(start_place, end_place, via_places),
            timeout=10,
        )
    except requests.Timeout:
        logger.exception("TMAP route optimization timed out")
        raise HTTPException(status_code=503, detail="TMAP API 요청 시간이 초과되었습니다.") from None
    except requests.RequestException as exc:
        logger.exception("TMAP route optimization request failed")
        raise HTTPException(status_code=503, detail=f"TMAP API 요청 실패: {exc}") from exc

    if response.status_code == 401:
        logger.error("TMAP authentication failed: %s", response.text)
        raise HTTPException(status_code=401, detail="TMAP API 인증에 실패했습니다.")
    if response.status_code >= 400:
        logger.error("TMAP route optimization failed: %s %s", response.status_code, response.text)
        raise HTTPException(status_code=502, detail="TMAP 경로 최적화 호출에 실패했습니다.")

    try:
        route_geojson = response.json()
    except ValueError:
        logger.exception("TMAP route optimization returned invalid JSON")
        raise HTTPException(status_code=502, detail="TMAP API 응답이 올바르지 않습니다.") from None

    features = route_geojson.get("features")
    if not isinstance(features, list):
        logger.error("TMAP route optimization response has no features: %s", route_geojson)
        raise HTTPException(status_code=502, detail="TMAP API 응답에 경로 정보가 없습니다.")

    return {
        "totalDistance": _sum_feature_metric(features, "distance"),
        "totalTime": _sum_feature_metric(features, "time"),
        "places": [
            {
                "order": index,
                "placeId": place["placeId"],
                "name": place["name"],
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "contentTypeId": place["contentTypeId"],
                "contentType": place["contentType"],
                "address": place["address"],
                "firstImage": place["firstImage"],
            }
            for index, place in enumerate(places, start=1)
        ],
        "routeGeoJson": {
            "type": route_geojson.get("type", "FeatureCollection"),
            "features": features,
        },
    }
