"""
Fix sourcetype enum in database to match Python model
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

def fix_sourcetype_enum():
    """Add missing values to sourcetype enum"""
    print("=" * 60)
    print("Fixing sourcetype enum")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Check current enum values
        print("\n1. Current enum values:")
        result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'sourcetype'
            )
            ORDER BY enumsortorder
        """))
        current_values = [row[0] for row in result]
        print(f"   {current_values}")
        
        # Values that should exist based on Python model
        required_values = ['youtube', 'openai', 'anthropic', 'blog']
        
        # Find missing values
        missing = [v for v in required_values if v not in current_values]
        
        if not missing:
            print("\n✅ All enum values already exist!")
            return
        
        print(f"\n2. Missing values: {missing}")
        print("\n3. Adding missing values...")
        
        # Add each missing value
        for value in missing:
            try:
                conn.execute(text(f"""
                    ALTER TYPE sourcetype ADD VALUE IF NOT EXISTS '{value}'
                """))
                conn.commit()
                print(f"   ✅ Added: {value}")
            except Exception as e:
                print(f"   ⚠️  {value}: {e}")
        
        # Verify final state
        print("\n4. Final enum values:")
        result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'sourcetype'
            )
            ORDER BY enumsortorder
        """))
        final_values = [row[0] for row in result]
        print(f"   {final_values}")
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)

if __name__ == "__main__":
    fix_sourcetype_enum()
