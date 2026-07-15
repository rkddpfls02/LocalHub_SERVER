import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
logger = logging.getLogger(__name__)


def build_prompt(query: str, tool_result: dict[str, Any]) -> str:
    """Build a relevance-ranking prompt using only SQLite candidates."""
    places = json.dumps(tool_result.get("results", []), ensure_ascii=False)
    return f"""사용자에게 부산 여행 장소를 추천하는 챗봇입니다.
아래 SQLite 검색 결과는 후보입니다. 사용자의 질문과 가장 관련 높은 장소부터 최대 3곳을
골라 순서대로 추천하세요. 반드시 후보에 있는 장소만 언급하고, 결과에 없는 장소, 운영 정보,
평점, 가격을 지어내지 마세요. 결과가 없으면 찾지 못했다고 간단히 안내하세요.

사용자 질문: {query}
추출 조건: location={tool_result.get("location")}, contentTypeIds={tool_result.get("contentTypeIds")}
검색 결과: {places}

각 추천에는 장소명, 주소, 질문과의 관련 이유를 한 문장으로 적으세요. 한국어로 답변하세요."""


def _fallback_answer(tool_result: dict[str, Any]) -> str:
    results = tool_result.get("results", [])
    if not results:
        return "조건에 맞는 장소를 찾지 못했습니다. 다른 지역이나 카테고리로 다시 검색해 주세요."
    lines = [f"- {item['title']} ({item['address']})" for item in results[:3]]
    return "검색 결과입니다.\n" + "\n".join(lines)


def generate_answer(query: str, tool_result: dict[str, Any]) -> str:
    """Generate a grounded answer, with a deterministic answer when no LLM is configured."""
    if not tool_result.get("results"):
        answer = _fallback_answer(tool_result)
        logger.info("GPT_ANSWER status=SKIPPED reason=NO_TOOL_RESULTS fallback_answer=%r", answer)
        return answer

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        answer = _fallback_answer(tool_result)
        logger.warning("GPT_ANSWER status=SKIPPED reason=OPENAI_API_KEY_MISSING fallback_answer=%r", answer)
        return answer

    try:
        logger.info(
            "GPT_ANSWER_REQUEST query=%r tool_result_count=%d",
            query,
            tool_result.get("resultCount", 0),
        )
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=[
                {"role": "system", "content": "검색 결과에 근거해 정확하게 답하는 한국어 여행 챗봇입니다."},
                {"role": "user", "content": build_prompt(query, tool_result)},
            ],
        )
        answer = response.output_text.strip()
        if answer:
            logger.info("GPT_ANSWER_RESPONSE status=SUCCESS answer=%r", answer)
            return answer
        fallback = _fallback_answer(tool_result)
        logger.warning("GPT_ANSWER_RESPONSE status=FAILED reason=EMPTY_RESPONSE fallback_answer=%r", fallback)
        return fallback
    except Exception:
        fallback = _fallback_answer(tool_result)
        logger.exception("GPT_ANSWER status=FAILED fallback_answer=%r", fallback)
        return fallback
