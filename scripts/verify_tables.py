import sys
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, OpenAIArticle, AnthropicArticle, YouTubeVideo

# Load env vars
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/dbname"  # Generic placeholder
)

def verify():
    with open("verification_result.txt", "w", encoding="utf-8") as f:
        try:
            f.write(f"Connecting to {DATABASE_URL}\n")
            engine = create_engine(DATABASE_URL)
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            f.write(f"Found tables: {tables}\n")
            
            required = ["openai_articles", "anthropic_articles", "youtube_videos"]
            missing = [t for t in required if t not in tables]
            
            if missing:
                f.write(f"❌ Missing tables: {missing}\n")
                f.write("Attempting to create missing tables...\n")
                Base.metadata.create_all(bind=engine)
                tables_after = inspector.get_table_names()
                missing_after = [t for t in required if t not in tables_after]
                if missing_after:
                    f.write(f"❌ Failed to create tables: {missing_after}\n")
                else:
                    f.write("✅ Created missing tables successfully!\n")
            else:
                f.write("✅ All required tables exist!\n")
        except Exception as e:
            f.write(f"❌ Error: {str(e)}\n")

if __name__ == "__main__":
    verify()
