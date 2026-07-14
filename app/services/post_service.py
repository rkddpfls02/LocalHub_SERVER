from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.post_image import PostImage
from app.repositories.post_repository import PostRepository


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGES = 5
MAX_IMAGE_SIZE = 3 * 1024 * 1024


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


async def _build_images(files: list[UploadFile] | None) -> list[PostImage]:
    files = files or []
    if len(files) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail="이미지는 최대 5장까지 업로드할 수 있습니다.")
    images: list[PostImage] = []
    for upload in files:
        file_name = upload.filename or ""
        if Path(file_name).suffix.lower() not in ALLOWED_EXTENSIONS or upload.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="jpg, jpeg, png, webp 이미지만 업로드할 수 있습니다.")
        image_data = await upload.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="빈 이미지 파일은 업로드할 수 없습니다.")
        if len(image_data) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="이미지 파일은 장당 3MB 이하여야 합니다.")
        images.append(PostImage(file_name=file_name, content_type=upload.content_type, image_data=image_data))
    return images


def _validate_text(nickname: str, password: str, title: str, content: str) -> None:
    if not nickname.strip() or not password or not title.strip() or not content.strip():
        raise HTTPException(status_code=400, detail="nickname, password, title, content는 필수입니다.")


def _validate_rating(rating: int) -> None:
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="rating은 1~5 사이의 값이어야 합니다.")


async def create_post(db: Session, place_id: int, nickname: str, password: str, title: str, content: str, images: list[UploadFile] | None, rating: int = 5) -> Post:
    _validate_text(nickname, password, title, content)
    _validate_rating(rating)
    repository = PostRepository(db)
    if repository.get_place(place_id) is None:
        raise _not_found("존재하지 않는 장소입니다.")
    post = Post(place_id=place_id, nickname=nickname.strip(), password=password, title=title.strip(), content=content.strip(), rating=rating, images=await _build_images(images))
    return repository.save(post)


def list_posts(db: Session, place_id: int | None) -> list[Post]:
    repository = PostRepository(db)
    if place_id is not None and repository.get_place(place_id) is None:
        raise _not_found("존재하지 않는 장소입니다.")
    return repository.list_posts(place_id)


def get_post(db: Session, post_id: int) -> Post:
    post = PostRepository(db).get_post(post_id)
    if post is None:
        raise _not_found("게시글을 찾을 수 없습니다.")
    return post


def get_post_image(db: Session, image_id: int) -> PostImage:
    image = PostRepository(db).get_image(image_id)
    if image is None:
        raise _not_found("이미지를 찾을 수 없습니다.")
    return image


def verify_post_password(db: Session, post_id: int, password: str) -> None:
    post = get_post(db, post_id)
    if post.password != password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비밀번호가 일치하지 않습니다.")


async def update_post(db: Session, post_id: int, password: str, title: str, content: str, images: list[UploadFile] | None, rating: int | None = None) -> Post:
    post = get_post(db, post_id)
    if post.password != password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비밀번호가 일치하지 않습니다.")
    if not title.strip() or not content.strip():
        raise HTTPException(status_code=400, detail="title과 content는 필수입니다.")
    if rating is not None:
        _validate_rating(rating)
        post.rating = rating
    post.title = title.strip()
    post.content = content.strip()
    if images:
        post.images.clear()
        post.images.extend(await _build_images(images))
    return PostRepository(db).save(post)


def delete_post(db: Session, post_id: int, password: str) -> None:
    post = get_post(db, post_id)
    if post.password != password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비밀번호가 일치하지 않습니다.")
    PostRepository(db).delete(post)
