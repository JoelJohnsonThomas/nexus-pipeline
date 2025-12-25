"""
System health check - verify all components are working.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, SessionLocal
from app.cache.redis_client import get_redis_client
from app.queue import get_message_queue
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_database():
    """Check database connectivity"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        logger.info("✅ Database: Connected")
        return True
    except Exception as e:
        logger.error(f"❌ Database: Failed - {e}")
        return False


def check_pgvector():
    """Check pgvector extension"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            if result.fetchone():
                logger.info("✅ pgvector: Enabled")
                return True
            else:
                logger.error("❌ pgvector: Not installed")
                return False
    except Exception as e:
        logger.error(f"❌ pgvector: Check failed - {e}")
        return False


def check_redis():
    """Check Redis connectivity"""
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        logger.info("✅ Redis: Connected")
        return True
    except Exception as e:
        logger.error(f"❌ Redis: Failed - {e}")
        return False


def check_message_queue():
    """Check RQ queue"""
    try:
        mq = get_message_queue()
        stats = mq.get_queue_stats()
        logger.info(f"✅ Message Queue: Working")
        logger.info(f"   - Extraction queue: {stats['extraction']['count']} pending, {stats['extraction']['failed']} failed")
        logger.info(f"   - Summarization queue: {stats['summarization']['count']} pending, {stats['summarization']['failed']} failed")
        logger.info(f"   - Embedding queue: {stats['embedding']['count']} pending, {stats['embedding']['failed']} failed")
        return True
    except Exception as e:
        logger.error(f"❌ Message Queue: Failed - {e}")
        return False


def check_data_counts():
    """Check database record counts"""
    try:
        from app.database import Article, ArticleSummary, ArticleEmbedding, Source, EmailSubscription
        
        db = SessionLocal()
        
        article_count = db.query(Article).count()
        summary_count = db.query(ArticleSummary).count()
        embedding_count = db.query(ArticleEmbedding).count()
        source_count = db.query(Source).count()
        subscription_count = db.query(EmailSubscription).count()
        
        logger.info("✅ Database Records:")
        logger.info(f"   - Sources: {source_count}")
        logger.info(f"   - Articles: {article_count}")
        logger.info(f"   - Summaries: {summary_count}")
        logger.info(f"   - Embeddings: {embedding_count}")
        logger.info(f"   - Subscriptions: {subscription_count}")
        
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Record Count Check: Failed - {e}")
        return False


def check_environment():
    """Check environment variables"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_vars = [
        'DATABASE_URL',
        'REDIS_HOST',
        'GEMINI_API_KEY',
        'EMAIL_SENDER',
        'EMAIL_PASSWORD',
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"❌ Environment: Missing variables - {', '.join(missing)}")
        return False
    else:
        logger.info("✅ Environment: All required variables set")
        return True


def main():
    print("=" * 60)
    print("🏥 AI NEWS AGGREGATOR - HEALTH CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("")
    
    checks = [
        ("Environment Variables", check_environment),
        ("Database Connection", check_database),
        ("pgvector Extension", check_pgvector),
        ("Redis Cache", check_redis),
        ("Message Queue", check_message_queue),
        ("Database Records", check_data_counts),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ {name}: Unexpected error - {e}")
            results.append((name, False))
        print("")
    
    # Summary
    print("=" * 60)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:30s} {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some checks failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
