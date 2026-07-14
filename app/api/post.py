from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.place import PlaceSearchItem
from app.schemas.post import PostCreateResponse, PostDeleteRequest, PostDetailResponse, PostImageItem, PostListItem, PostListResponse
from app.services.post_service import create_post, delete_post, get_post, get_post_image, list_posts, update_post, verify_post_password
from app.services.place_service import search_places


router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/search", response_model=list[PlaceSearchItem])
def search(keyword: str | None = None, db: Session = Depends(get_db)):
    return search_places(db, keyword or "")


def _detail(post) -> PostDetailResponse:
    return PostDetailResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        nickname=post.nickname,
        place_id=post.place_id,
        rating=post.rating,
        images=[PostImageItem(image_id=image.id) for image in post.images],
    )


@router.post("", response_model=PostCreateResponse, status_code=201)
async def create(
    place_id: int = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(..., ge=1, le=5),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    post = await create_post(
        db,
        place_id,
        nickname,
        password,
        title,
        content,
        images,
        rating=rating,
    )
    return PostCreateResponse(
        id=post.id,
        message="게시글이 등록되었습니다."
    )


@router.get("", response_model=PostListResponse)
def list_all(place_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    posts = list_posts(db, place_id)
    return PostListResponse(total=len(posts), items=[PostListItem(id=post.id, title=post.title, nickname=post.nickname, place_id=post.place_id, rating=post.rating, image_count=len(post.images), created_at=post.created_at) for post in posts])


@router.get("/images/{image_id}")
def read_image(image_id: int, db: Session = Depends(get_db)):
    image = get_post_image(db, image_id)
    return StreamingResponse(BytesIO(image.image_data), media_type=image.content_type)


@router.get("/{post_id}", response_model=PostDetailResponse)
def read(post_id: int, db: Session = Depends(get_db)):
    return _detail(get_post(db, post_id))


@router.post("/{post_id}/verify-password", status_code=status.HTTP_204_NO_CONTENT)
def verify_password(post_id: int, payload: PostDeleteRequest, db: Session = Depends(get_db)):
    verify_post_password(db, post_id, payload.password)


@router.put("/{post_id}", response_model=PostDetailResponse)
async def update(post_id: int, password: str = Form(...), title: str = Form(...), content: str = Form(...), rating: int | None = Form(default=None, ge=1, le=5), images: List[UploadFile] = File(default=[]), db: Session = Depends(get_db)):
    return _detail(await update_post(db, post_id, password, title, content, images, rating=rating))


@router.delete("/{post_id}", status_code=204)
def delete(post_id: int, payload: PostDeleteRequest, db: Session = Depends(get_db)):
    delete_post(db, post_id, payload.password)
