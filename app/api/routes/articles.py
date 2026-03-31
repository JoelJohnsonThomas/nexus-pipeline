"""
GET /articles?q=<query> — semantic search endpoint.

Encodes the query with the same sentence-transformers model used during
ingestion, then finds the most similar articles via pgvector cosine distance.
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class ArticleResult(BaseModel):
    id: int
    title: str
    url: str
    published_at: Optional[datetime]
    source_name: Optional[str]
    summary: Optional[str]
    key_points: Optional[List[str]]
    similarity: float


@router.get("/articles", response_model=List[ArticleResult], tags=["articles"])
def search_articles(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
):
    """
    Semantic similarity search over article embeddings.

    Requires pgvector to be installed and at least one article with an embedding.
    Returns articles ordered by cosine similarity to the query.
    """
    try:
        from sentence_transformers import SentenceTransformer
        from app.config import settings
        from app.database import SessionLocal, Article, ArticleEmbedding, ArticleSummary
        from app.database.models import Source
        from sqlalchemy import text

        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        query_vec = model.encode(q).tolist()
        query_vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

        db = SessionLocal()
        try:
            rows = db.execute(
                text("""
                    SELECT
                        a.id,
                        a.title,
                        a.url,
                        a.published_at,
                        s.name AS source_name,
                        sm.summary,
                        sm.key_points,
                        1 - (ae.embedding <=> CAST(:qvec AS vector)) AS similarity
                    FROM article_embeddings ae
                    JOIN articles a ON a.id = ae.article_id
                    JOIN sources s ON s.id = a.source_id
                    LEFT JOIN article_summaries sm ON sm.article_id = a.id
                    ORDER BY ae.embedding <=> CAST(:qvec AS vector)
                    LIMIT :limit
                """),
                {"qvec": query_vec_str, "limit": limit},
            ).fetchall()
        finally:
            db.close()

        return [
            ArticleResult(
                id=row.id,
                title=row.title,
                url=row.url,
                published_at=row.published_at,
                source_name=row.source_name,
                summary=row.summary,
                key_points=row.key_points,
                similarity=float(row.similarity),
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
