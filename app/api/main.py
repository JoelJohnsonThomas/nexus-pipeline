"""
NexusFeed API

A lightweight FastAPI service that exposes:
  GET /health  — component health status (DB, Redis, queues, counts)
  GET /articles — semantic similarity search over article embeddings

Run locally:
    uvicorn app.api.main:app --reload

Or via Docker Compose:
    docker compose up api
"""
from fastapi import FastAPI

from app.api.routes import health, articles

app = FastAPI(
    title="NexusFeed API",
    description="AI news aggregator — health checks and semantic article search",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(articles.router)
