# AI News Aggregator - System Health Check

## 📋 Manual Verification Checklist

### ✅ Component Status

#### 1. Database Setup
**Files to check:**
- [ ] Docker container is running: `docker ps` (should see postgres container)
- [ ] Database connection works: Run `python scripts/test_db_connection.py`
- [ ] Tables are created: Run `python scripts/verify_tables.py`

**Expected tables:**
- `sources` - News and video sources
- `articles` - All scraped articles (unified)
- `openai_articles` - Legacy OpenAI-specific table
- `anthropic_articles` - Legacy Anthropic-specific table
- `youtube_videos` - Legacy YouTube-specific table
- `google_articles` - Google Blog articles (if created)

**Current Database Config:**
- Host: `localhost`
- Port: `5433` (Docker mapping)
- Database: `newsaggregator`
- User: `newsaggregator`
- Password: `newspassword`

---

#### 2. Scrapers
All scrapers are located in `app/scrapers/`:

**✅ Implemented Scrapers:**
1. **Google Blog Scraper** (`google_scraper.py`)
   - RSS URL: https://blog.google/rss
   - Status: ✅ Recently added
   - Test: `python app/scrapers/google_scraper.py`

2. **OpenAI Scraper** (`openai_scraper.py`)
   - RSS URL: https://openai.com/news/rss.xml
   - Status: ✅ Implemented
   - Test: Run via `run_scrapers.py`

3. **Anthropic Scraper** (`anthropic_scraper.py`)
   - Multiple RSS feeds (research/engineering/news)
   - Status: ✅ Implemented
   - Test: Run via `run_scrapers.py`

4. **YouTube Scraper** (`youtube_scraper.py`)
   - Scrapes configured channels
   - Status: ✅ Implemented
   - Config: `config/youtube_channels.json`
   - Test: `python test_youtube_scraper.py`

---

#### 3. Database Sources
Check if sources are properly seeded:

**Required sources in database:**
```bash
python scripts/verify_tables.py
```

Should show sources for:
- Google Blog (https://blog.google/rss)
- OpenAI (https://openai.com/news/rss.xml)
- Anthropic Research/Engineering/News feeds
- YouTube channels (as configured)

**Add missing sources:**
If Google Blog source is missing:
```bash
python scripts/seed_google_source.py
```

For other sources:
```bash
python scripts/add_source.py
```

---

#### 4. Configuration
**Environment Variables** (in `.env` file):

**Required:**
- [ ] `GEMINI_API_KEY` - For LLM summarization
- [ ] `EMAIL_SENDER` - Sender email address
- [ ] `EMAIL_PASSWORD` - App password for email
- [ ] `EMAIL_RECIPIENT` - Recipient email address

**Optional:**
- [ ] `DATABASE_URL` - Override default DB connection
- [ ] `GEMINI_MODEL` - Default: `gemini-1.5-flash`
- [ ] `SMTP_HOST` - Default: `smtp.gmail.com`
- [ ] `SMTP_PORT` - Default: `587`
- [ ] `DIGEST_HOURS_BACK` - Default: `24`
- [ ] `TIMEZONE` - Default: `America/New_York`

---

#### 5. Main Scripts

**1. Database Initialization**
```bash
# Initialize database tables
python scripts/init_db.py
```

**2. Run All Scrapers**
```bash
# Run with default 24-hour lookback
python run_scrapers.py

# Run with 7-day lookback
python run_scrapers.py --hours 168

# Include YouTube transcripts (slower)
python run_scrapers.py --transcripts

# Dry run (don't save to database)
python run_scrapers.py --no-save

# Verbose output
python run_scrapers.py --verbose
```

**3. Generate and Send Digest**
```bash
# Generate digest from last 24 hours
python main.py

# Or schedule it via cron/task scheduler
```

---

## 🧪 Quick Test Procedure

### Step 1: Start Docker
```bash
cd docker
docker-compose up -d
```

### Step 2: Verify Database Connection
```bash
python scripts/test_db_connection.py
```
Expected: ✅ SUCCESS: Connected to port 5433!

### Step 3: Initialize/Verify Tables
```bash
python scripts/verify_tables.py
```
Expected: Should list all tables and row counts

### Step 4: Seed Sources (if needed)
```bash
# Add Google Blog source
python scripts/seed_google_source.py

# Verify sources exist
python scripts/verify_tables.py
```

### Step 5: Test Individual Scrapers

**Google Blog:**
```bash
python app/scrapers/google_scraper.py
```

**YouTube:**
```bash
python test_youtube_scraper.py
```

### Step 6: Run Full Scraper Suite
```bash
python run_scrapers.py --hours 168
```
Expected output:
```
📺 YOUTUBE SCRAPER
  → Found X videos

🤖 OPENAI SCRAPER
  → Found X articles

🧠 ANTHROPIC SCRAPER
  → Found X articles

🔎 GOOGLE BLOG SCRAPER
  → Found X articles

📊 FINAL SUMMARY
...
```

### Step 7: Test Email Digest (Optional)
```bash
python main.py
```
Expected: Email sent to configured recipient

---

## 🔧 Common Issues and Fixes

### Issue 1: Database Connection Failed
**Error:** `Connection refused` or `password authentication failed`

**Fix:**
1. Check if Docker is running: `docker ps`
2. Start Docker if not running: `cd docker && docker-compose up -d`
3. Verify port is 5433: Check `app/config.py` line 17
4. Check credentials match docker-compose.yml

### Issue 2: Source Not Found
**Error:** `Source not found, skipping database save`

**Fix:**
Run the appropriate seed script:
```bash
python scripts/seed_google_source.py
python scripts/add_source.py  # For other sources
```

### Issue 3: Import Errors
**Error:** `ModuleNotFoundError`

**Fix:**
Install dependencies:
```bash
pip install -r requirements.txt
# OR if using uv
uv sync
```

### Issue 4: No Articles Found
**Possible causes:**
1. Time window too narrow - try `--hours 168` (7 days)
2. RSS feeds might be temporarily unavailable
3. Rate limiting from the source

### Issue 5: Email Not Sending
**Check:**
1. Gmail app password is correct (not regular password)
2. 2FA is enabled on Gmail account
3. SMTP settings are correct
4. Check firewall/network restrictions

---

## 📊 Expected File Structure

```
AI-NEWS-AGGREGATOR/
├── app/
│   ├── config.py              # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── create_tables.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── email/
│   │   └── email_sender.py
│   ├── llm/
│   │   └── summarizer.py
│   └── scrapers/
│       ├── anthropic_scraper.py
│       ├── google_scraper.py    ✅ NEW
│       ├── openai_scraper.py
│       ├── youtube_scraper.py
│       └── scraper_manager.py
├── config/
│   └── youtube_channels.json
├── scripts/
│   ├── add_source.py
│   ├── init_db.py
│   ├── seed_google_source.py   ✅ NEW
│   ├── test_db_connection.py
│   └── verify_tables.py
├── docker/
│   ├── docker-compose.yml
│   └── init.sql
├── .env                         # Environment variables
├── main.py                      # Main digest generator
├── run_scrapers.py             # Scraper runner (includes Google) ✅ UPDATED
└── verify_all.py               # Comprehensive verification script ✅ NEW
```

---

## ✅ Success Indicators

Your system is working properly if:

1. ✅ Docker container is running
2. ✅ Database connection succeeds
3. ✅ All expected tables exist
4. ✅ All sources are seeded in database
5. ✅ Individual scrapers run without errors
6. ✅ `run_scrapers.py` completes successfully
7. ✅ Articles are saved to database (check counts with `verify_tables.py`)
8. ✅ Email digest sends successfully (optional, requires email config)

---

## 🚀 Quick Start Commands

```bash
# 1. Start database
cd docker && docker-compose up -d

# 2. Verify connection
python scripts/test_db_connection.py

# 3. Initialize database
python scripts/init_db.py

# 4. Verify tables
python scripts/verify_tables.py

# 5. Seed Google source (if missing)
python scripts/seed_google_source.py

# 6. Run scrapers (7 days of data)
python run_scrapers.py --hours 168

# 7. Generate and send digest
python main.py
```

---

**Last Updated:** December 7, 2024
**Database Port:** 5433
**Recent Changes:** Added Google Blog scraper and source seeding
