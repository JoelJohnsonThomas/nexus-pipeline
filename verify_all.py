"""
Comprehensive verification script for AI News Aggregator
Tests all major components: database, scrapers, and configuration
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def test_imports():
    """Test if all required modules can be imported"""
    print_section("1. Testing Imports")
    
    modules = [
        ('app.config', 'Config'),
        ('app.database', 'get_db_connection'),
        ('app.scrapers.google_scraper', 'GoogleScraper'),
        ('app.scrapers.openai_scraper', 'OpenAIScraper'),
        ('app.scrapers.anthropic_scraper', 'AnthropicScraper'),
        ('app.scrapers.youtube_scraper', 'YoutubeScraper'),
    ]
    
    results = []
    for module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_path}.{class_name}")
            results.append(True)
        except Exception as e:
            print(f"✗ {module_path}.{class_name}: {str(e)}")
            results.append(False)
    
    return all(results)

def test_config():
    """Test configuration loading"""
    print_section("2. Testing Configuration")
    
    try:
        from app.config import config
        
        print(f"Database URL: {config.DATABASE_URL[:50]}...")
        print(f"Gemini Model: {config.GEMINI_MODEL}")
        print(f"SMTP Host: {config.SMTP_HOST}")
        print(f"SMTP Port: {config.SMTP_PORT}")
        print(f"Timezone: {config.TIMEZONE}")
        
        # Check for API keys (without revealing them)
        has_gemini = bool(config.GEMINI_API_KEY)
        has_email_pwd = bool(config.EMAIL_PASSWORD)
        has_email_sender = bool(config.EMAIL_SENDER)
        has_email_recipient = bool(config.EMAIL_RECIPIENT)
        
        print(f"\nAPI Keys Status:")
        print(f"  Gemini API Key: {'✓ Set' if has_gemini else '✗ Not set'}")
        print(f"  Email Sender: {'✓ Set' if has_email_sender else '✗ Not set'}")
        print(f"  Email Password: {'✓ Set' if has_email_pwd else '✗ Not set'}")
        print(f"  Email Recipient: {'✓ Set' if has_email_recipient else '✗ Not set'}")
        
        if not all([has_gemini, has_email_pwd, has_email_sender, has_email_recipient]):
            print("\n⚠ Warning: Some configuration values are missing")
            return False
        
        print("\n✓ All configuration values are set")
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {str(e)}")
        return False

def test_database():
    """Test database connection and tables"""
    print_section("3. Testing Database Connection")
    
    try:
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version[:50]}...")
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n✓ Found {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")
        
        cursor.close()
        conn.close()
        
        # Check for expected tables
        expected_tables = ['sources', 'openai_articles', 'anthropic_articles', 
                          'youtube_videos', 'google_articles']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"\n⚠ Warning: Missing tables: {', '.join(missing_tables)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        return False

def test_scrapers():
    """Test scraper initialization (without actually scraping)"""
    print_section("4. Testing Scrapers")
    
    scrapers = {
        'Google': 'app.scrapers.google_scraper.GoogleScraper',
        'OpenAI': 'app.scrapers.openai_scraper.OpenAIScraper',
        'Anthropic': 'app.scrapers.anthropic_scraper.AnthropicScraper',
        'YouTube': 'app.scrapers.youtube_scraper.YoutubeScraper',
    }
    
    results = []
    for name, scraper_path in scrapers.items():
        try:
            module_path, class_name = scraper_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            scraper_class = getattr(module, class_name)
            
            # Try to instantiate
            scraper = scraper_class()
            print(f"✓ {name} scraper: OK")
            results.append(True)
        except Exception as e:
            print(f"✗ {name} scraper: {str(e)}")
            results.append(False)
    
    return all(results)

def test_main_script():
    """Check if main scripts exist and are valid Python"""
    print_section("5. Testing Main Scripts")
    
    scripts = [
        'run_scrapers.py',
        'main.py',
        'scripts/init_db.py',
        'scripts/seed_google_source.py',
    ]
    
    results = []
    for script in scripts:
        script_path = project_root / script
        if script_path.exists():
            try:
                # Try to compile the script
                with open(script_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), script_path, 'exec')
                print(f"✓ {script}: Valid Python file")
                results.append(True)
            except Exception as e:
                print(f"✗ {script}: Syntax error - {str(e)}")
                results.append(False)
        else:
            print(f"✗ {script}: File not found")
            results.append(False)
    
    return all(results)

def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print(" AI News Aggregator - Comprehensive Verification")
    print("="*60)
    
    results = {
        'Imports': test_imports(),
        'Configuration': test_config(),
        'Database': test_database(),
        'Scrapers': test_scrapers(),
        'Scripts': test_main_script(),
    }
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s}: {status}")
        all_passed = all_passed and passed
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED - System is working properly!")
    else:
        print("✗ SOME TESTS FAILED - Please review the errors above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
