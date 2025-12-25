# 🤖 AI News Aggregator

**Production-ready AI-powered news aggregation system with intelligent summarization and automated email digests.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## 🎯 What It Does

An automated pipeline that:
- **Scrapes** AI news from YouTube, RSS feeds, and websites
- **Extracts** full content from articles and video transcripts  
- **Summarizes** using Google Gemini 2.5-flash LLM
- **Generates** vector embeddings for semantic search
- **Sends** personalized HTML email digests

---

## 🏗️ Architecture

```mermaid
graph LR
    A[Scrapers] -->|Articles| B[Message Queue]
    B --> C[Workers]
    C -->|Extract| D[Content]
    D -->|Summarize| E[Gemini LLM]
    E -->|Embed| F[Vector DB]
    F --> G[Email Digest]
    
    style E fill:#ff6b6b
    style F fill:#4ecdc4
```

**Tech Stack:**
- **Database:** PostgreSQL + pgvector for embeddings
- **Cache:** Redis for API responses  
- **Queue:** RQ (Redis Queue) for async processing
- **LLM:** Google Gemini 2.5-flash
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **Email:** Gmail SMTP with Jinja2 templates

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Gmail account (for sending emails)
- Google Gemini API key

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/AI-NEWS-AGGREGATOR.git
cd AI-NEWS-AGGREGATOR

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies (using uv - recommended)
pip install uv
uv pip install .

# Or use pip
pip install -e .
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add:
# - GEMINI_API_KEY (from https://aistudio.google.com/app/apikey)
# - EMAIL_SENDER (your Gmail)
# - EMAIL_PASSWORD (Gmail App Password from https://myaccount.google.com/apppasswords)
```

### 3. Start Infrastructure

```bash
cd docker
docker-compose up -d

# Verify services running
docker-compose ps
```

### 4. Initialize Database

```bash
# Create tables
python scripts/init_tables.py

# Add performance indexes
python scripts/optimize_database.py

# Seed news sources
python scripts/seed_sources.py
```

### 5. Health Check

```bash
python scripts/health_check.py
```

Expected output:
```
✅ Database: Connected
✅ pgvector: Enabled
✅ Redis: Connected
✅ Message Queue: Working
✅ Database Records: ...
```

---

## 📖 Usage

### Scrape Articles

```bash
# Scrape last 24 hours
python run_scrapers_with_pipeline.py --hours 24

# Scrape last week
python run_scrapers_with_pipeline.py --hours 168
```

### Start Worker (Process Articles)

```bash
# In a separate terminal
python scripts/run_workers.py
```

Worker automatically processes articles through:
1. Content extraction
2. LLM summarization
3. Vector embedding generation

### Send Email Digest

```bash
# Add your email subscription
python scripts/seed_subscription.py

# Send test digest
python scripts/send_digest_now.py --test

# Send to all subscribers
python scripts/send_digest_now.py --all --hours 24
```

---

## 📁 Project Structure

```
AI-NEWS-AGGREGATOR/
├── app/
│   ├── scrapers/          # YouTube, RSS, web scrapers
│   ├── processing/        # Content extraction, LLM, embeddings
│   ├── orchestrator/      # Worker functions, pipeline logic
│   ├── email/             # Templates, rendering, sending
│   ├── database/          # SQLAlchemy models
│   ├── queue/             # RQ message queue client
│   └── cache/             # Redis caching
├── scripts/
│   ├── run_workers.py     # Start RQ workers
│   ├── seed_sources.py    # Add news sources to DB
│   ├── seed_subscription.py  # Add email subscriber
│   ├── send_digest_now.py    # Manual digest sender
│   ├── health_check.py       # System health verification
│   └── optimize_database.py  # Add performance indexes
├── docker/
│   └── docker-compose.yml # PostgreSQL + Redis
├── .env                   # Configuration (not in git)
└── pyproject.toml         # Dependencies
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://newsaggregator:password@localhost:5433/newsaggregator
POSTGRES_USER=newsaggregator
POSTGRES_PASSWORD=your-password
POSTGRES_DB=newsaggregator

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Google Gemini LLM
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# Email
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EMAIL_RECIPIENT=recipient@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Gmail App Password Setup

1. Go to [Google Account App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and your device
3. Click "Generate"
4. Copy the 16-character password to `.env` as `EMAIL_PASSWORD`

---

## 🧪 Testing

### Health Check

```bash
python scripts/health_check.py
```

### Email Testing

```bash
# Test templates only (no email sent)
python scripts/test_email.py --template-test

# Test SMTP connection
python scripts/test_email.py --smtp-test --recipient your@email.com

# Full end-to-end test
python scripts/test_email.py --full-test --recipient your@email.com
```

### Integration Test

```bash
python scripts/test_pipeline.py
```

---

## 🔍 Features

### Multi-Source Scraping
- **YouTube:** Channel RSS feeds with video metadata
- **OpenAI:** RSS feed from OpenAI blog
- **Anthropic:** Web scraping research/engineering/news pages
- **Google Blog:** RSS feed

### Intelligent Processing
- **Content Extraction:** Full-text from articles, transcripts from videos
- **LLM Summarization:** AI-generated summaries with key points
- **Vector Embeddings:** Semantic search capability (384-dimensional)

### Email Delivery
- Professional HTML templates with responsive design
- Plain text fallback
- Subscriber management (CRUD)
- Scheduling support (manual or cron)

### Performance
- Asynchronous processing with RQ workers
- Redis caching for API responses
- Database indexes for fast queries
- Batch embedding generation

---

## 🛠️ Development

### Adding a New Source

1. Create scraper in `app/scrapers/your_scraper.py`
2. Add source to database via `seed_sources.py`
3. Register in `run_scrapers.py`

### Adding a Worker Function

1. Create function in `app/orchestrator/workers.py`
2. Register queue in `scripts/run_workers.py`
3. Enqueue job via `app/queue/client.py`

---

## 📊 Database Schema

**Core Tables:**
- `sources` - News sources (YouTube channels, RSS feeds)
- `articles` - Scraped articles/videos
- `article_summaries` - LLM-generated summaries
- `article_embeddings` - Vector embeddings
- `processing_queue` - Pipeline job tracking
- `email_subscriptions` - Email subscribers
- `email_deliveries` - Delivery logs

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps

# Check connection
python -c "from app.database import engine; engine.connect(); print('OK')"
```

### Worker Not Processing

```bash
# Check Redis is running
python -c "from app.cache.redis_client import get_redis_client; get_redis_client().ping(); print('OK')"

# Check queue stats
python -c "from app.queue import get_message_queue; print(get_message_queue().get_queue_stats())"
```

### Email Not Sending

- Verify Gmail App Password (not regular password)
- Check 2FA is enabled on Google account
- Review `EMAIL_SENDER` and `EMAIL_PASSWORD` in `.env`

### No Articles Found

```bash
# Scrape with longer lookback period
python run_scrapers_with_pipeline.py --hours 168

# Check if sources are seeded
python -c "from app.database import SessionLocal, Source; print(SessionLocal().query(Source).count())"
```

---

## 📝 Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `init_tables.py` | Create database schema | `python scripts/init_tables.py` |
| `seed_sources.py` | Add news sources | `python scripts/seed_sources.py` |
| `seed_subscription.py` | Add email subscriber | `python scripts/seed_subscription.py` |
| `run_workers.py` | Start processing workers | `python scripts/run_workers.py` |
| `run_scrapers.py` | Run all scrapers | `python run_scrapers.py` |
| `send_digest_now.py` | Send email digest | `python scripts/send_digest_now.py --all` |
| `health_check.py` | Verify system health | `python scripts/health_check.py` |
| `optimize_database.py` | Add performance indexes | `python scripts/optimize_database.py` |
| `test_email.py` | Test email system | `python scripts/test_email.py --full-test` |

---

## 🚀 Deployment

### Option 1: Local with Cron

```bash
# Linux/Mac crontab
# Daily digest at 8am
0 8 * * * cd /path/to/project && python scripts/send_digest_now.py --all

# Scrape every 6 hours
0 */6 * * * cd /path/to/project && python run_scrapers_with_pipeline.py --hours 6
```

### Option 2: Docker Production

```bash
# Build image
docker build -t ai-news-aggregator .

# Run worker
docker run -d --env-file .env ai-news-aggregator python scripts/run_workers.py

# Run scheduler (cron container)
docker run -d --env-file .env ai-news-aggregator cron
```

---

## 📈 Performance Metrics

**Typical Processing Times:**
- Scraping: 2-5 seconds per source
- Content Extraction: 1-3 seconds per article
- LLM Summarization: 5-10 seconds per article (Gemini 2.5-flash)
- Embedding Generation: 0.5-2 seconds per article
- Digest Email: 1-3 seconds per recipient

**Capacity:**
- Handles 1000+ articles/day
- Gmail SMTP: 500 emails/day limit
- Gemini API: 60 requests/minute free tier

---

## 📄 License

MIT License - see LICENSE file

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 🙏 Acknowledgments

- **Google Gemini** for LLM summarization
- **Sentence Transformers** for embeddings
- **pgvector** for vector search
- **RQ** for async job processing

---

## 📮 Contact

For issues or questions, please open a GitHub issue.

**Happy news aggregating! 🚀**