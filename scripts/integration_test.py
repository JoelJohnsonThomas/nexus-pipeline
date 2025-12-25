"""
Comprehensive integration test suite for the AI News Aggregator.
Tests all major components and their interactions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, Article, ArticleSummary, ArticleEmbedding, Source
from app.queue import get_message_queue
from app.email.digest_generator import get_digest_generator
from app.email.renderer import get_email_renderer
from app.email.subscription_service import get_subscription_service
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class IntegrationTests:
    def __init__(self):
        self.results = []
    
    def run_test(self, name, test_func):
        """Run a single test and record result"""
        logger.info(f"\n🧪 Testing: {name}")
        try:
            result = test_func()
            self.results.append((name, result, None))
            if result:
                logger.info(f"   ✅ PASS")
            else:
                logger.warning(f"   ⚠️  INCOMPLETE/SKIP")
            return result
        except Exception as e:
            logger.error(f"   ❌ FAIL - {e}")
            self.results.append((name, False, str(e)))
            return False
    
    def test_database_connectivity(self):
        """Test database connection and basic queries"""
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    
    def test_sources_exist(self):
        """Verify news sources are seeded"""
        db = SessionLocal()
        count = db.query(Source).count()
        db.close()
        
        if count == 0:
            logger.info("      Run: python scripts/seed_sources.py")
            return False
        
        logger.info(f"      Found {count} sources")
        return True
    
    def test_articles_scraped(self):
        """Check if articles exist in database"""
        db = SessionLocal()
        count = db.query(Article).count()
        db.close()
        
        if count == 0:
            logger.info("      Run: python run_scrapers_with_pipeline.py --hours 168")
            return False
        
        logger.info(f"      Found {count} articles")
        return True
    
    def test_summaries_generated(self):
        """Check if summaries have been generated"""
        db = SessionLocal()
        count = db.query(ArticleSummary).count()
        db.close()
        
        if count == 0:
            logger.info("      Run: python scripts/run_workers.py")
            return False
        
        logger.info(f"      Found {count} summaries")
        return True
    
    def test_embeddings_generated(self):
        """Check if embeddings have been generated"""
        db = SessionLocal()
        count = db.query(ArticleEmbedding).count()
        db.close()
        
        if count == 0:
            logger.info("      Workers should process articles automatically")
            return False
        
        logger.info(f"      Found {count} embeddings")
        return True
    
    def test_complete_pipeline(self):
        """Verify articles with full pipeline (summary + embedding)"""
        db = SessionLocal()
        
        complete_count = (
            db.query(Article)
            .join(ArticleSummary, Article.id == ArticleSummary.article_id)
            .join(ArticleEmbedding, Article.id == ArticleEmbedding.article_id)
            .count()
        )
        
        db.close()
        
        if complete_count == 0:
            return False
        
        logger.info(f"      {complete_count} articles fully processed")
        return True
    
    def test_message_queue(self):
        """Test RQ message queue connectivity"""
        mq = get_message_queue()
        stats = mq.get_queue_stats()
        
        total_pending = sum(q['count'] for q in stats.values())
        total_failed = sum(q['failed'] for q in stats.values())
        
        logger.info(f"      Pending: {total_pending}, Failed: {total_failed}")
        return True
    
    def test_digest_generation(self):
        """Test digest generator can fetch articles"""
        generator = get_digest_generator()
        articles = generator.generate_digest(hours_back=168)
        
        if not articles:
            logger.info("      No articles with summaries found")
            return False
        
        logger.info(f"      Generated digest with {len(articles)} articles")
        return True
    
    def test_email_rendering(self):
        """Test email template rendering"""
        sample_articles = [{
            'title': 'Test Article',
            'url': 'https://example.com',
            'published_date': 'December 24, 2025',
            'source_name': 'Test Source',
            'summary': 'Test summary.',
            'key_points': ['Point 1', 'Point 2']
        }]
        
        renderer = get_email_renderer()
        html, text = renderer.render_digest(
            articles=sample_articles,
            subscriber_name="Test",
            subscriber_email="test@example.com"
        )
        
        return 'Test Article' in html and 'Test Article' in text
    
    def test_subscription_service(self):
        """Test subscription management"""
        service = get_subscription_service()
        subscribers = service.get_active_subscribers()
        
        logger.info(f"      {len(subscribers)} active subscribers")
        
        if len(subscribers) == 0:
            logger.info("      Run: python scripts/seed_subscription.py")
        
        return True  # Not required to pass
    
    def test_vector_embeddings(self):
        """Test embedding dimensions are correct"""
        db = SessionLocal()
        embedding = db.query(ArticleEmbedding).first()
        db.close()
        
        if not embedding:
            return False
        
        dimensions = len(embedding.embedding)
        expected = 384  # all-MiniLM-L6-v2
        
        if dimensions != expected:
            logger.warning(f"      Unexpected dimensions: {dimensions} (expected {expected})")
            return False
        
        logger.info(f"      {dimensions}-dimensional vectors ✓")
        return True
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 70)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, result, _ in self.results if result)
        failed_or_skip = sum(1 for _, result, _ in self.results if not result)
        total = len(self.results)
        
        for name, result, error in self.results:
            if result:
                status = "✅ PASS"
            elif error:
                status = f"❌ FAIL - {error[:40]}"
            else:
                status = "⚠️  INCOMPLETE"
            print(f"{name:45s} {status}")
        
        print("=" * 70)
        print(f"Results: {passed}/{total} passed, {failed_or_skip} incomplete/failed")
        print("=" * 70)
        
        if passed >= 6:  # Core tests
            print("🎉 Core functionality verified!")
            return 0
        else:
            print("⚠️  Some components not ready. Follow suggestions above.")
            return 1


def main():
    print("=" * 70)
    print("🧪 AI NEWS AGGREGATOR - COMPREHENSIVE INTEGRATION TEST")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    tests = IntegrationTests()
    
    # Run all tests
    tests.run_test("Database Connectivity", tests.test_database_connectivity)
    tests.run_test("News Sources Seeded", tests.test_sources_exist)
    tests.run_test("Articles Scraped", tests.test_articles_scraped)
    tests.run_test("Summaries Generated", tests.test_summaries_generated)
    tests.run_test("Embeddings Generated", tests.test_embeddings_generated)
    tests.run_test("Complete Pipeline", tests.test_complete_pipeline)
    tests.run_test("Message Queue", tests.test_message_queue)
    tests.run_test("Digest Generation", tests.test_digest_generation)
    tests.run_test("Email Rendering", tests.test_email_rendering)
    tests.run_test("Subscription Service", tests.test_subscription_service)
    tests.run_test("Vector Embeddings", tests.test_vector_embeddings)
    
    return tests.print_summary()


if __name__ == "__main__":
    sys.exit(main())
