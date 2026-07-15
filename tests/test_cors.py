from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.cors import DEFAULT_ALLOWED_ORIGINS, get_allowed_origins


def make_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEFAULT_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/chat")
    def chat() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


def test_cors_allows_deployed_and_local_frontend_origins():
    client = make_client()
    for origin in ("https://buriburi16.netlify.app", "http://localhost:5173"):
        response = client.options(
            "/chat",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.headers["access-control-allow-origin"] == origin


def test_cors_does_not_allow_unlisted_origins():
    response = make_client().options(
        "/chat",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_allow_origins_can_be_configured_with_environment_variable(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://example.com/, https://admin.example.com")

    assert get_allowed_origins() == ["https://example.com", "https://admin.example.com"]
