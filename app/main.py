from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_title, lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
