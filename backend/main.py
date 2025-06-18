from contextlib import asynccontextmanager

from backend.db import MongoDBClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import charts


@asynccontextmanager
async def lifespan(app: FastAPI):
    await MongoDBClient.get_client()
    yield
    await MongoDBClient.close_client()

app = FastAPI(lifespan=lifespan)
app.include_router(charts.router, prefix="/api/v1")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

