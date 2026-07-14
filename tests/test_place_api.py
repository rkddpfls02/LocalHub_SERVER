import sqlite3

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
    assert posts_response.json() == {"total": 0, "items": []}
    assert chat_response.status_code == 200
    assert "answer" in chat_response.json()
