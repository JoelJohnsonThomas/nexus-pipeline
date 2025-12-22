"""
Enhanced scraper runner with automatic pipeline integration.
Scrapes articles and automatically enqueues them for processing.
"""
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

import argparse
import logging
from run_scrapers import main as run_scrapers_main
from app.orchestrator.pipeline import ArticlePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_with_pipeline(hours_back: int = 24, transcripts: bool = False, no_save: bool = False):
    """
    Run scrapers and automatically process articles through the pipeline.
    
    Args:
        hours_back: Hours to look back for articles
        transcripts: Include YouTube transcripts
        no_save: Don't save to database (dry run)
    """
    logger.info("=" * 60)
    logger.info("SCRAPER + PIPELINE RUN")
    logger.info("=" * 60)
    
    # Run scrapers
    logger.info("\n1️⃣  Running scrapers...")
    sys.argv = [
        'run_scrapers_with_pipeline.py',
        '--hours', str(hours_back),
    ]
    
    if transcripts:
        sys.argv.append('--transcripts')
    if no_save:
        sys.argv.append('--no-save')
    
    # Run the scrapers
    run_scrapers_main()
    
    if no_save:
        logger.info("\n⚠️  Dry run mode - skipping pipeline processing")
        return
    
    # Process new articles through pipeline
    logger.info("\n2️⃣  Processing articles through pipeline...")
    pipeline = ArticlePipeline()
    
    results = pipeline.process_new_articles(hours_back=hours_back)
    
    logger.info(f"\n📊 Pipeline Results:")
    logger.info(f"  Found: {results.get('found', 0)} new articles")
    logger.info(f"  Enqueued: {results.get('enqueued', 0)}")
    logger.info(f"  Failed: {results.get('failed', 0)}")
    
    if results.get('enqueued', 0) > 0:
        logger.info("\n✅ Articles enqueued for processing!")
        logger.info("\n📝 Next steps:")
        logger.info("  1. Start workers to process the queue:")
        logger.info("     python scripts/run_workers.py")
        logger.info("\n  2. Or run in burst mode (processes and exits):")
        logger.info("     python scripts/run_workers.py --burst")
        logger.info("\n  3. Monitor progress:")
        logger.info("     python scripts/test_pipeline.py")
    else:
        logger.info("\n⚠️  No new articles to process")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run scrapers and process articles through pipeline'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Hours to look back (default: 24)'
    )
    parser.add_argument(
        '--transcripts',
        action='store_true',
        help='Include YouTube transcripts'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Dry run mode'
    )
    
    args = parser.parse_args()
    run_with_pipeline(args.hours, args.transcripts, args.no_save)
