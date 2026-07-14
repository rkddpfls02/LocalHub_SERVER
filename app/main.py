import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.place import router as place_router
from app.api.post import router as post_router
from app.db.database import init_db

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(title="LocalHub Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(chat_router)
app.include_router(place_router)
app.include_router(post_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "LocalHub Server is running",
        "chat_endpoint": "/chat",
    }
