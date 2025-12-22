"""
RQ Worker Runner
Starts Redis Queue workers to process pipeline jobs.
"""
import sys
import os
from pathlib import Path
import argparse
import logging

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from redis import Redis
from rq import Worker, Queue, SimpleWorker
from rq.job import Job
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start RQ workers"""
    parser = argparse.ArgumentParser(description='Start RQ workers for article processing')
    parser.add_argument(
        '--queues',
        nargs='+',
        default=['extraction', 'summarization', 'embedding', 'email'],
        help='Queues to listen to (default: all)'
    )
    parser.add_argument(
        '--burst',
        action='store_true',
        help='Run in burst mode (exit when queue is empty)'
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Worker name (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    # Connect to Redis
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    
    try:
        redis_conn = Redis(host=redis_host, port=redis_port)
        redis_conn.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)
    
    # Create queue objects
    queues = [Queue(name, connection=redis_conn) for name in args.queues]
    
    logger.info(f"Starting worker for queues: {args.queues}")
    if args.burst:
        logger.info("Running in BURST mode (will exit when queues are empty)")
    
    # Detect platform and use appropriate worker
    is_windows = platform.system() == 'Windows'
    
    if is_windows:
        logger.info("Windows detected: Using SimpleWorker (no forking)")
        worker_class = SimpleWorker
    else:
        logger.info("Unix/Linux detected: Using Worker (with forking)")
        worker_class = Worker
    
    # Create and start worker
    worker = worker_class(
        queues,
        connection=redis_conn,
        name=args.name
    )
    
    try:
        worker.work(burst=args.burst)
    except KeyboardInterrupt:
        logger.info("\nWorker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
