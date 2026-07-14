from fastapi import FastAPI

from app.db.database import init_db

app = FastAPI(title="LocalHub Server")

init_db()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "LocalHub Server is running"}
