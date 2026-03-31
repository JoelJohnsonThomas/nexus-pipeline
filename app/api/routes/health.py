"""
GET /health — system health endpoint.

Returns the status of each subsystem (database, pgvector, Redis, queues)
so monitoring tools can poll it instead of requiring a human to run the
health_check.py script manually.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    checks: Dict[str, Any]


def _check_database() -> dict:
    try:
        from sqlalchemy import text
        from app.database.base import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check_pgvector() -> dict:
    try:
        from sqlalchemy import text
        from app.database.base import engine
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            found = result.fetchall()
        return {"ok": bool(found), "installed": bool(found)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check_redis() -> dict:
    try:
        from app.cache.redis_client import get_redis_client
        client = get_redis_client()
        client.client.ping()
        return {"ok": True, "host": client.host, "port": client.port}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check_queues() -> dict:
    try:
        from app.queue import get_message_queue
        mq = get_message_queue()
        stats = mq.get_queue_stats()
        return {"ok": True, "stats": stats}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check_counts() -> dict:
    try:
        from app.database import SessionLocal, Article, ArticleSummary, ArticleEmbedding, Source
        db = SessionLocal()
        try:
            return {
                "ok": True,
                "sources": db.query(Source).count(),
                "articles": db.query(Article).count(),
                "summaries": db.query(ArticleSummary).count(),
                "embeddings": db.query(ArticleEmbedding).count(),
            }
        finally:
            db.close()
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/health", response_model=HealthResponse, tags=["operations"])
def health_check() -> HealthResponse:
    """
    Check the health of all system components.
    Returns 200 even when some checks fail — inspect the 'status' field.
    """
    checks = {
        "database": _check_database(),
        "pgvector": _check_pgvector(),
        "redis": _check_redis(),
        "queues": _check_queues(),
        "counts": _check_counts(),
    }

    all_ok = all(v.get("ok", False) for v in checks.values())
    any_ok = any(v.get("ok", False) for v in checks.values())

    if all_ok:
        status = "healthy"
    elif any_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(status=status, checks=checks)
