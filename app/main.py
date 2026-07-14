from fastapi import FastAPI

app = FastAPI(title="LocalHub Server")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "LocalHub Server is running"}
