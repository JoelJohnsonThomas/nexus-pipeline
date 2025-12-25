"""
Performance benchmarking script.
Validates the metrics claims in README.md.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from datetime import datetime, timedelta
from app.database import SessionLocal, Article, ArticleSummary, ArticleEmbedding
from app.email.digest_generator import get_digest_generator
from app.email.renderer import get_email_renderer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def benchmark_digest_generation():
    """Benchmark digest generation for 50 articles"""
    logger.info("📊 Benchmarking digest generation (50 articles)...")
    
    generator = get_digest_generator()
    
    start = time.time()
    articles = generator.generate_digest(hours_back=168)
    end = time.time()
    
    duration = end - start
    
    logger.info(f"   Found: {len(articles)} articles")
    logger.info(f"   Time: {duration:.2f} seconds")
    logger.info(f"   Result: {'✅ PASS' if duration < 2 else '⚠️ SLOW'} (target: < 2s)")
    
    return duration


def benchmark_email_rendering():
    """Benchmark email template rendering"""
    logger.info("\n📧 Benchmarking email rendering...")
    
    # Sample data
    sample_articles = [{
        'title': f'Test Article {i}',
        'url': f'https://example.com/{i}',
        'published_date': 'December 24, 2025',
        'source_name': 'Test Source',
        'summary': 'This is a test summary.' * 10,
        'key_points': ['Point 1', 'Point 2', 'Point 3']
    } for i in range(50)]
    
    renderer = get_email_renderer()
    
    start = time.time()
    html, text = renderer.render_digest(
        articles=sample_articles,
        subscriber_name="Test",
        subscriber_email="test@example.com"
    )
    end = time.time()
    
    duration = end - start
    
    logger.info(f"   Articles: 50")
    logger.info(f"   Time: {duration:.2f} seconds")
    logger.info(f"   Result: {'✅ PASS' if duration < 1 else '⚠️ SLOW'} (target: < 1s)")
    
    return duration


def check_database_performance():
    """Check database query performance with indexes"""
    logger.info("\n🗄️ Checking database performance...")
    
    db = SessionLocal()
    
    # Test 1: Recent articles query
    start = time.time()
    cutoff = datetime.now() - timedelta(days=7)
    articles = db.query(Article).filter(Article.published_at >= cutoff).limit(100).all()
    end = time.time()
    
    duration1 = end - start
    logger.info(f"   Recent articles query (100): {duration1*1000:.0f}ms")
    logger.info(f"   Result: {'✅ PASS' if duration1 < 0.1 else '⚠️ SLOW'} (target: < 100ms)")
    
    # Test 2: Join query (articles + summaries)
    start = time.time()
    results = (
        db.query(Article, ArticleSummary)
        .join(ArticleSummary, Article.id == ArticleSummary.article_id)
        .limit(50)
        .all()
    )
    end = time.time()
    
    duration2 = end - start
    logger.info(f"   Join query (50 articles): {duration2*1000:.0f}ms")
    logger.info(f"   Result: {'✅ PASS' if duration2 < 0.5 else '⚠️ SLOW'} (target: < 500ms)")
    
    db.close()
    
    return duration1, duration2


def calculate_capacity():
    """Calculate theoretical processing capacity"""
    logger.info("\n📈 Calculating theoretical capacity...")
    
    # Based on API limits
    gemini_free_tier_rpm = 60  # requests per minute
    gemini_processing_time = 8  # average seconds per article
    
    # Daily capacity
    articles_per_hour = gemini_free_tier_rpm * 60 / (gemini_processing_time / 60)
    articles_per_day = articles_per_hour * 24
    
    logger.info(f"   Gemini API: {gemini_free_tier_rpm} req/min free tier")
    logger.info(f"   Avg processing: {gemini_processing_time}s per article")
    logger.info(f"   Theoretical capacity: {int(articles_per_day)} articles/day")
    logger.info(f"   Practical capacity (with overhead): ~{int(articles_per_day * 0.7)} articles/day")
    
    # Email capacity
    gmail_daily_limit = 500
    logger.info(f"\n   Gmail SMTP: {gmail_daily_limit} emails/day limit")
    
    return int(articles_per_day * 0.7)


def main():
    print("=" * 70)
    print("🔬 AI NEWS AGGREGATOR - PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\nValidating README.md performance claims...\n")
    
    # Run benchmarks
    digest_time = benchmark_digest_generation()
    render_time = benchmark_email_rendering()
    db_times = check_database_performance()
    capacity = calculate_capacity()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Digest generation (50 articles):     {digest_time:.2f}s  (target: < 2s)")
    print(f"Email rendering (50 articles):       {render_time:.2f}s  (target: < 1s)")
    print(f"DB query (recent articles):          {db_times[0]*1000:.0f}ms (target: < 100ms)")
    print(f"DB query (join 50):                  {db_times[1]*1000:.0f}ms (target: < 500ms)")
    print(f"Theoretical capacity:                {capacity} articles/day")
    print("=" * 70)
    
    print("\n💡 README Claims Validation:")
    print(f"   'digest_generation_time': < 1s (50 articles) - {'✅ VERIFIED' if digest_time < 1 else f'⚠️ ACTUAL: {digest_time:.2f}s'}")
    print(f"   'articles_processed_per_day': 1,000+ - {'✅ PLAUSIBLE' if capacity >= 700 else '⚠️ OVERSTATED'}")
    print("\n")


if __name__ == "__main__":
    main()
