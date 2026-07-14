import sqlite3
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.chat import router as chat_router
from app.api.place import router as place_router
from app.api.post import router as post_router
from app.db.database import Base, get_db
from app.models.place import Place
from app.models.post import Post


@pytest.fixture()
def client(tmp_path):
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    db.add_all(
        [
            Place(
                id=15,
                content_id="126081",
                region="부산",
                content_type="관광지",
                content_type_id=12,
                title="해운대해수욕장",
                addr1="부산광역시 해운대구 해운대해변로 264",
                addr2="(우동)",
                first_image="https://example.com/haeundae.jpg",
            ),
            Place(
                id=323,
                content_id="126078",
                region="부산",
                content_type="관광지",
                content_type_id=12,
                title="광안리해수욕장",
                addr1="부산광역시 수영구 광안해변로 219 (광안동)",
                addr2="",
                first_image="https://example.com/gwangalli.jpg",
            ),
        ]
    )
    created_at = datetime(2026, 7, 15, 1, 0, 0)
    updated_at = datetime(2026, 7, 15, 1, 5, 0)
    db.add(
        Post(
            id=1,
            place_id=15,
            nickname="tester",
            password="secret",
            title="원본 제목",
            content="원본 내용",
            rating=5,
            created_at=created_at,
            updated_at=updated_at,
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        test_db = TestingSessionLocal()
        try:
            yield test_db
        finally:
            test_db.close()

    app = FastAPI()
    app.include_router(chat_router)
    app.include_router(place_router)
    app.include_router(post_router)
    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    test_client.localhub_app = app
    test_client.testing_session_factory = TestingSessionLocal

    yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_real_tourism_db_contains_reference_content_id():
    connection = sqlite3.connect("file:tourism.db?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT id, content_id FROM places WHERE content_id = ?",
            ("126081",),
        ).fetchone()
    finally:
        connection.close()

    assert row == (15, "126081")


def test_get_place_by_content_id_success(client):
    response = client.get("/places/by-content-id/126081")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 15
    assert body["content_id"] == "126081"
    assert body["title"] == "해운대해수욕장"
    assert body["region"] == "부산"
    assert body["content_type"] == "관광지"
    assert body["content_type_id"] == 12
    assert body["addr1"] == "부산광역시 해운대구 해운대해변로 264"
    assert body["addr2"] == "(우동)"
    assert body["first_image"] == "https://example.com/haeundae.jpg"


def test_get_place_by_content_id_not_found(client):
    response = client.get("/places/by-content-id/not-found")

    assert response.status_code == 404
    assert response.json() == {"detail": "장소를 찾을 수 없습니다."}


def test_existing_posts_search_still_works(client):
    response = client.get("/posts/search", params={"keyword": "해운대"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 15,
            "content_id": "126081",
            "title": "해운대해수욕장",
            "address": "부산광역시 해운대구 해운대해변로 264 (우동)",
        }
    ]


def test_existing_posts_and_chat_routes_are_still_registered(client):
    posts_response = client.get("/posts", params={"place_id": 15})
    chat_response = client.post("/chat", json={"query": "해운대 관광지 추천"})

    assert posts_response.status_code == 200
    assert posts_response.json()["total"] == 1
    assert chat_response.status_code == 200
    assert "answer" in chat_response.json()


def test_verify_post_password_success_does_not_change_post(client):
    before = client.get("/posts/1").json()
    session = client.testing_session_factory()
    try:
        before_updated_at = session.get(Post, 1).updated_at
    finally:
        session.close()

    response = client.post("/posts/1/verify-password", json={"password": "secret"})

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/posts/1").json() == before

    session = client.testing_session_factory()
    try:
        post = session.get(Post, 1)
        assert post.title == "원본 제목"
        assert post.content == "원본 내용"
        assert post.rating == 5
        assert post.updated_at == before_updated_at
    finally:
        session.close()


def test_verify_post_password_wrong_password_does_not_change_post(client):
    before = client.get("/posts/1").json()
    session = client.testing_session_factory()
    try:
        before_updated_at = session.get(Post, 1).updated_at
    finally:
        session.close()

    response = client.post("/posts/1/verify-password", json={"password": "wrong"})

    assert response.status_code == 403
    assert response.json() == {"detail": "비밀번호가 일치하지 않습니다."}
    assert client.get("/posts/1").json() == before

    session = client.testing_session_factory()
    try:
        assert session.get(Post, 1).updated_at == before_updated_at
    finally:
        session.close()


def test_verify_post_password_missing_post(client):
    response = client.post("/posts/999/verify-password", json={"password": "secret"})

    assert response.status_code == 404
    assert response.json() == {"detail": "게시글을 찾을 수 없습니다."}


def test_update_still_verifies_password(client):
    response = client.put(
        "/posts/1",
        data={"password": "wrong", "title": "수정 제목", "content": "수정 내용", "rating": "4"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "비밀번호가 일치하지 않습니다."}


def test_delete_still_verifies_password_and_succeeds_with_correct_password(client):
    wrong_response = client.request("DELETE", "/posts/1", json={"password": "wrong"})
    right_response = client.request("DELETE", "/posts/1", json={"password": "secret"})

    assert wrong_response.status_code == 403
    assert wrong_response.json() == {"detail": "비밀번호가 일치하지 않습니다."}
    assert right_response.status_code == 204
