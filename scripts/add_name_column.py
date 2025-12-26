"""
Add name column to email_subscriptions table
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

def add_name_column():
    """Add name column to email_subscriptions if it doesn't exist"""
    print("Adding name column to email_subscriptions table...")
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='email_subscriptions' 
                AND column_name='name'
            """))
            
            if result.fetchone():
                print("✅ Column 'name' already exists")
                return
            
            # Add column
            conn.execute(text("""
                ALTER TABLE email_subscriptions 
                ADD COLUMN name VARCHAR(255)
            """))
            conn.commit()
            
            print("✅ Successfully added 'name' column to email_subscriptions")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    add_name_column()
