"""
Dead Letter Queue inspector and replay tool.

Usage:
    # Show all unplayed dead letters
    python scripts/replay_dead_letters.py

    # Show details for a specific entry
    python scripts/replay_dead_letters.py --id 42

    # Replay a specific dead letter
    python scripts/replay_dead_letters.py --id 42 --replay

    # Replay all un-replayed entries for a specific queue
    python scripts/replay_dead_letters.py --queue extraction --replay

    # Replay all un-replayed entries since a date
    python scripts/replay_dead_letters.py --since 2025-01-01 --replay

    # Dry-run (show what would be replayed without enqueuing)
    python scripts/replay_dead_letters.py --replay --dry-run
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, DeadLetter
from app.queue import get_message_queue


def list_dead_letters(db, queue: str = None, since: datetime = None, replayed: bool = False):
    query = db.query(DeadLetter)
    if queue:
        query = query.filter(DeadLetter.queue_name == queue)
    if since:
        query = query.filter(DeadLetter.failed_at >= since)
    if not replayed:
        query = query.filter(DeadLetter.replayed == False)  # noqa: E712
    return query.order_by(DeadLetter.failed_at.desc()).all()


def print_entry(entry: DeadLetter):
    print(
        f"  id={entry.id} | article_id={entry.article_id} | queue={entry.queue_name} "
        f"| retries={entry.retry_count} | failed_at={entry.failed_at.isoformat()}"
    )
    print(f"    error: {entry.error_message}")
    print(f"    payload: {entry.payload}")
    if entry.replayed:
        print(f"    replayed_at: {entry.replayed_at.isoformat()}")


def replay_entry(entry: DeadLetter, mq, dry_run: bool = False) -> bool:
    """Re-enqueue a dead letter based on its queue_name."""
    article_id = entry.article_id
    if article_id is None:
        print(f"  [skip] id={entry.id}: article_id is NULL (article deleted)")
        return False

    if dry_run:
        print(f"  [dry-run] Would re-enqueue article {article_id} → {entry.queue_name}")
        return True

    if entry.queue_name == "extraction":
        mq.enqueue_extraction(article_id)
    elif entry.queue_name == "summarization":
        model = entry.payload.get("model")
        mq.enqueue_summarization(article_id, model=model)
    elif entry.queue_name == "embedding":
        mq.enqueue_embedding(article_id)
    else:
        print(f"  [skip] id={entry.id}: unknown queue '{entry.queue_name}'")
        return False

    print(f"  [replayed] id={entry.id}: article {article_id} → {entry.queue_name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Inspect and replay dead letter queue entries")
    parser.add_argument("--id", type=int, help="Target a specific dead letter by ID")
    parser.add_argument("--queue", help="Filter by queue name (extraction/summarization/embedding)")
    parser.add_argument("--since", help="Filter entries failed since DATE (YYYY-MM-DD)")
    parser.add_argument("--show-replayed", action="store_true", help="Include already-replayed entries")
    parser.add_argument("--replay", action="store_true", help="Re-enqueue matching entries")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be replayed without enqueuing")
    args = parser.parse_args()

    since_dt = None
    if args.since:
        since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)

    db = SessionLocal()
    try:
        if args.id:
            entries = db.query(DeadLetter).filter(DeadLetter.id == args.id).all()
        else:
            entries = list_dead_letters(db, queue=args.queue, since=since_dt, replayed=args.show_replayed)

        if not entries:
            print("No dead letter entries found matching criteria.")
            return

        print(f"\nFound {len(entries)} dead letter entr{'y' if len(entries) == 1 else 'ies'}:\n")
        for entry in entries:
            print_entry(entry)
            print()

        if args.replay:
            mq = get_message_queue()
            replayed_count = 0
            for entry in entries:
                if entry.replayed and not args.id:
                    continue
                if replay_entry(entry, mq, dry_run=args.dry_run):
                    if not args.dry_run:
                        entry.replayed = True
                        entry.replayed_at = datetime.utcnow()
                    replayed_count += 1

            if not args.dry_run:
                db.commit()

            action = "Would replay" if args.dry_run else "Replayed"
            print(f"\n{action} {replayed_count} entr{'y' if replayed_count == 1 else 'ies'}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
