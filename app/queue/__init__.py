"""Queue package for AI News Aggregator."""
from app.queue.client import MessageQueue, get_message_queue

__all__ = ["MessageQueue", "get_message_queue"]
