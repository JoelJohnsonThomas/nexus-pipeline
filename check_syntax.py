"""
Quick syntax check for all Python files in the project
"""
import os
import py_compile
from pathlib import Path

def check_python_file(file_path):
    """Check if a Python file has valid syntax"""
    try:
        py_compile.compile(file_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    project_root = Path(__file__).parent
    
    # Key files to check
    files_to_check = [
        # Main scripts
        "run_scrapers.py",
        "main.py",
        
        # Scrapers
        "app/scrapers/google_scraper.py",
        "app/scrapers/openai_scraper.py",
        "app/scrapers/anthropic_scraper.py",
        "app/scrapers/youtube_scraper.py",
        
        # Database
        "app/database/__init__.py",
        "app/database/models.py",
        "app/database/repository.py",
        "app/database/create_tables.py",
        
        # Config
        "app/config.py",
        
        # Scripts
        "scripts/init_db.py",
        "scripts/seed_google_source.py",
        "scripts/test_db_connection.py",
        "scripts/verify_tables.py",
        
        # Email
        "app/email/email_sender.py",
    ]
    
    print("=" * 60)
    print("PYTHON SYNTAX VERIFICATION")
    print("=" * 60)
    print()
    
    all_valid = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"⚠  {file_path}: FILE NOT FOUND")
            all_valid = False
            continue
        
        is_valid, error = check_python_file(full_path)
        if is_valid:
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            print(f"  Error: {error}")
            all_valid = False
    
    print()
    print("=" * 60)
    if all_valid:
        print("✅ ALL FILES HAVE VALID PYTHON SYNTAX")
    else:
        print("❌ SOME FILES HAVE ERRORS")
    print("=" * 60)
    
    return 0 if all_valid else 1

if __name__ == "__main__":
    exit(main())
