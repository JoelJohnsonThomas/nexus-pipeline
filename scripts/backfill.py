"""
Backfill script — re-enqueue articles for reprocessing.

Use this when you change the embedding model, switch LLM model, or need to
re-run a pipeline stage for a set of articles.

Usage examples:
    # Re-summarize all articles processed with an old Gemini model
    python scripts/backfill.py --model gemini-1.5-flash

    # Re-process all articles scraped since a date (full pipeline from extraction)
    python scripts/backfill.py --since 2025-01-01

    # Re-run only the summarization stage for articles in a date range
    python scripts/backfill.py --since 2025-06-01 --stage summarization

    # Dry-run: see what would be enqueued without enqueuing
    python scripts/backfill.py --model gemini-1.5-flash --dry-run
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func
from app.database import SessionLocal, Article, ProcessingQueue, ProcessingStatus
from app.database.models_extended import ArticleSummary
from app.queue import get_message_queue


STAGES = ("extraction", "summarization", "embedding")


def get_articles_by_model(db, model_name: str):
    """Find articles summarized with a specific LLM model."""
    return (
        db.query(Article)
        .join(ArticleSummary, ArticleSummary.article_id == Article.id)
        .filter(ArticleSummary.model == model_name)
        .all()
    )


def get_articles_since(db, since: datetime):
    """Find articles scraped on or after the given date."""
    return db.query(Article).filter(Article.scraped_at >= since).all()


def reset_and_enqueue(article, stage: str, mq, dry_run: bool = False) -> bool:
    """Reset an article's ProcessingQueue entry and re-enqueue it."""
    if dry_run:
        print(f"  [dry-run] article {article.id}: '{article.title[:60]}' → {stage}")
        return True

    db = SessionLocal()
    try:
        pq = db.query(ProcessingQueue).filter(ProcessingQueue.article_id == article.id).first()
        if pq:
            pq.status = ProcessingStatus.PENDING
            pq.retry_count = 0
            pq.error_message = None
            pq.current_stage = stage
            pq.completed_at = None
        else:
            pq = ProcessingQueue(
                article_id=article.id,
                status=ProcessingStatus.PENDING,
                current_stage=stage,
                retry_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(pq)
        db.commit()
    finally:
        db.close()

    if stage == "extraction":
        mq.enqueue_extraction(article.id)
    elif stage == "summarization":
        mq.enqueue_summarization(article.id)
    elif stage == "embedding":
        mq.enqueue_embedding(article.id)

    print(f"  [enqueued] article {article.id}: '{article.title[:60]}' → {stage}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Re-enqueue articles for pipeline reprocessing")
    parser.add_argument(
        "--model", metavar="MODEL_NAME",
        help="Re-summarize all articles whose ArticleSummary.model matches this value "
             "(e.g. 'gemini-1.5-flash')",
    )
    parser.add_argument(
        "--since", metavar="DATE",
        help="Re-process all articles scraped on or after this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--stage", choices=STAGES, default=None,
        help="Pipeline stage to re-run from (default: extraction for --since, "
             "summarization for --model)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be enqueued without actually enqueuing",
    )
    args = parser.parse_args()

    if not args.model and not args.since:
        parser.error("At least one of --model or --since is required.")

    db = SessionLocal()
    try:
        articles = []

        if args.model:
            found = get_articles_by_model(db, args.model)
            print(f"Found {len(found)} articles with model='{args.model}'")
            articles.extend(found)

        if args.since:
            since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
            # Strip timezone for comparison with naive DB timestamps
            since_naive = since_dt.replace(tzinfo=None)
            found = get_articles_since(db, since_naive)
            print(f"Found {len(found)} articles scraped since {args.since}")
            # Deduplicate
            seen = {a.id for a in articles}
            articles.extend(a for a in found if a.id not in seen)

        if not articles:
            print("No articles matched the given criteria. Nothing to do.")
            return

        # Determine default stage
        stage = args.stage
        if stage is None:
            stage = "summarization" if args.model and not args.since else "extraction"

        print(f"\nWill re-enqueue {len(articles)} article(s) starting from stage: {stage}")
        if args.dry_run:
            print("(dry-run — no changes will be made)\n")
        else:
            mq = get_message_queue()

        count = 0
        for article in articles:
            mq_arg = None if args.dry_run else mq
            if reset_and_enqueue(article, stage, mq_arg, dry_run=args.dry_run):
                count += 1

        action = "Would enqueue" if args.dry_run else "Enqueued"
        print(f"\n{action} {count} article(s) for {stage}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
