"""
Centralized logging configuration for NexusFeed.

Set LOG_FORMAT=json in the environment to get structured JSON output suitable
for log aggregation systems (CloudWatch, Datadog, etc.). The default format is
human-readable for local development.
"""
import logging
import os
import sys


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure root logger with either JSON or human-readable format.

    Call this once at application startup before any other logging occurs.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    log_format = os.getenv("LOG_FORMAT", "text").lower()

    if log_format == "json":
        try:
            from pythonjsonlogger.jsonlogger import JsonFormatter
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                JsonFormatter(
                    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                )
            )
            logging.basicConfig(level=level, handlers=[handler], force=True)
            return
        except ImportError:
            pass  # Fall through to text format if library not installed

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
