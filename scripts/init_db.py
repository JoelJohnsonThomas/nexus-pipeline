"""
Database initialization script.
"""
import sys
import logging

from app.database import init_db, drop_all_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database tables"""
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    
    response = input("\nThis will create all database tables. Continue? (y/n): ")
    
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    try:
        init_db()
        print("\n✅ Database initialized successfully!")
        print("\nNext steps:")
        print("1. Add news sources using: python scripts/add_source.py")
        print("2. Test scraping: python main.py --mode test-scrape")
        print("3. Run full workflow: python main.py --mode run")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        sys.exit(1)


def reset_database():
    """Drop and recreate all tables (DANGEROUS!)"""
    print("=" * 60)
    print("⚠️  DATABASE RESET - THIS WILL DELETE ALL DATA!")
    print("=" * 60)
    
    response = input("\nAre you ABSOLUTELY sure? Type 'DELETE ALL DATA' to confirm: ")
    
    if response != 'DELETE ALL DATA':
        print("Aborted.")
        return
    
    try:
        drop_all_tables()
        init_db()
        print("\n✅ Database reset complete!")
    except Exception as e:
        logger.error(f"❌ Error resetting database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization")
    parser.add_argument('--reset', action='store_true', help='Reset database (DELETE ALL DATA)')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        main()
