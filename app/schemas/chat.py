from pydantic import BaseModel, Field


class SearchPlacesRequest(BaseModel):
    query: str = Field(..., description="사용자 자연어 질문")


class SearchPlacesResponse(BaseModel):
    location: str | None = None
    contentTypeIds: list[int] = []
    message: str | None = None
