"""
Test script to verify infrastructure setup.
Tests database connection, Redis connection, and basic functionality.
"""
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_database():
    """Test database connection"""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        print("🔄 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected: PostgreSQL {version.split()[1]}")
            
            # Test pgvector
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("✅ pgvector extension is available")
            else:
                print("⚠️ pgvector extension not installed yet")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_redis():
    """Test Redis connection"""
    try:
        from app.cache import get_redis_client
        
        print("\n🔄 Testing Redis connection...")
        redis_client = get_redis_client()
        
        # Test set/get
        redis_client.set("test_key", "test_value", 10)
        value = redis_client.get("test_key", deserialize=False)
        
        if value == "test_value":
            print("✅ Redis connected and working")
            
            # Get stats
            stats = redis_client.get_stats()
            print(f"   Memory used: {stats.get('used_memory_human', 'N/A')}")
            print(f"   Connected clients: {stats.get('connected_clients', 'N/A')}")
        else:
            print("⚠️ Redis connected but test failed")
        
        # Cleanup
        redis_client.delete("test_key")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"   Make sure Redis is running (docker-compose up redis)")
        return False


def test_message_queue():
    """Test message queue"""
    try:
        from app.queue import get_message_queue
        
        print("\n🔄 Testing message queue...")
        mq = get_message_queue()
        
        # Get queue stats
        stats = mq.get_queue_stats()
        print("✅ Message queue connected")
        print(f"   Extraction queue: {stats['extraction']['count']} jobs")
        print(f"   Summarization queue: {stats['summarization']['count']} jobs")
        print(f"   Embedding queue: {stats['embedding']['count']} jobs")
        print(f"   Email queue: {stats['email']['count']} jobs")
        
        return True
    except Exception as e:
        print(f"❌ Message queue test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Infrastructure Test Suite")
    print("=" * 60)
    
    results = {
        'database': test_database(),
        'redis': test_redis(),
        'message_queue': test_message_queue(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:20} {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All infrastructure tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
