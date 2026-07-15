import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.place import Place


load_dotenv()
logger = logging.getLogger(__name__)

# 한국관광공사 TourAPI content type ID
CATEGORY_MAP = {
    "관광지": 12,
    "문화시설": 14,
    "축제": 15,
    "행사": 15,
    "공연": 15,
    "여행코스": 25,
    "레포츠": 28,
    "액티비티": 28,
    "숙박": 32,
    "호텔": 32,
    "펜션": 32,
    "게스트하우스": 32,
    "쇼핑": 38,
    "시장": 38,
    "백화점": 38,
    "음식점": 39,
    "맛집": 39,
    "카페": 39,
}

VALID_CONTENT_TYPE_IDS = frozenset(CATEGORY_MAP.values())


def _fallback_extract_search_condition(query: str) -> dict[str, Any]:
    """Extract deterministic filters when an LLM is unavailable."""
    content_type_ids = list(dict.fromkeys(
        category_id for keyword, category_id in CATEGORY_MAP.items() if keyword in query
    ))
    return {"location": None, "contentTypeIds": content_type_ids}


def _normalise_condition(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"location": None, "contentTypeIds": []}

    location = value.get("location")
    location = location.strip() if isinstance(location, str) and location.strip() else None
    raw_ids = value.get("contentTypeIds", [])
    if not isinstance(raw_ids, list):
        raw_ids = []
    content_type_ids = list(dict.fromkeys(
        item for item in raw_ids if isinstance(item, int) and item in VALID_CONTENT_TYPE_IDS
    ))
    return {"location": location, "contentTypeIds": content_type_ids}


def _parse_json_object(text: str) -> dict[str, Any] | None:
    """Accept an object even if the model accidentally wraps it in a code fence."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def extract_search_condition(query: str) -> dict[str, Any]:
    """Return the location and TourAPI content type filters for a user question."""
    fallback = _fallback_extract_search_condition(query)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            "GPT_CONDITION_EXTRACT status=SKIPPED reason=OPENAI_API_KEY_MISSING fallback=%s",
            fallback,
        )
        return fallback

    try:
        logger.info("GPT_CONDITION_EXTRACT_REQUEST query=%r", query)
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=[
                {
                    "role": "system",
                    "content": (
                        "사용자 질문에서 관광 장소 검색 조건을 추출하세요. "
                        "반드시 JSON 객체만 반환합니다. 형식: "
                        '{"location": string | null, "contentTypeIds": number[]}. '
                        "location에는 질문에 나온 지역명·동네명·관광지 주변 지역명을 원문 그대로 넣고, "
                        "질문에 지역이 없으면 null을 넣으세요. 임의로 지역을 추측하지 마세요. "
                        "contentTypeIds는 관광지=12, 문화시설=14, 축제/행사/공연=15, "
                        "여행코스=25, 레포츠/액티비티=28, 숙박=32, 쇼핑=38, 음식점/카페=39만 사용하세요."
                    ),
                },
                {"role": "user", "content": query},
            ],
        )
        condition = _parse_json_object(response.output_text.strip())
        if condition is None:
            logger.warning(
                "GPT_CONDITION_EXTRACT status=FAILED reason=INVALID_JSON fallback=%s raw_response=%r",
                fallback,
                response.output_text,
            )
            return fallback
        parsed = _normalise_condition(condition)
        # 카테고리 키워드는 결정적으로 보완하되, 지역은 반드시 모델이 추출한 값을 사용한다.
        result = {
            "location": parsed["location"],
            "contentTypeIds": parsed["contentTypeIds"] or fallback["contentTypeIds"],
        }
        logger.info("GPT_CONDITION_EXTRACT_RESPONSE status=SUCCESS condition=%s", result)
        return result
    except Exception:
        logger.exception("GPT_CONDITION_EXTRACT status=FAILED fallback=%s", fallback)
        return fallback


def search_places(db: Session, query: str, limit: int = 30) -> dict[str, Any]:
    """Search SQLite Place rows using the filters extracted from a natural-language query."""
    condition = extract_search_condition(query)
    location = condition["location"]
    content_type_ids = condition["contentTypeIds"]
    logger.info(
        "TOOL_CALL name=search_places status=START location=%r content_type_ids=%s limit=%d",
        location,
        content_type_ids,
        limit,
    )

    query_obj = db.query(Place)
    if content_type_ids:
        query_obj = query_obj.filter(Place.content_type_id.in_(content_type_ids))
    if location:
        location_filter = f"%{location}%"
        query_obj = query_obj.filter(or_(
            Place.addr1.like(location_filter),
            Place.addr2.like(location_filter),
        ))

    try:
        places = query_obj.order_by(Place.id).limit(limit).all()
    except Exception:
        logger.exception("TOOL_CALL_RESULT name=search_places status=FAILED")
        raise
    result = {
        "location": location,
        "contentTypeIds": content_type_ids,
        "resultCount": len(places),
        "results": [
            {
                "id": place.id,
                "title": place.title,
                "address": " ".join(part for part in (place.addr1, place.addr2) if part),
                "contentTypeId": place.content_type_id,
                "contentType": place.content_type,
                "region": place.region,
            }
            for place in places
        ],
        "message": "장소 후보 검색을 완료했습니다.",
    }
    logger.info(
        "TOOL_CALL_RESULT name=search_places status=SUCCESS result_count=%d results=%s",
        result["resultCount"],
        result["results"],
    )
    return result
