# AI News Aggregator 🤖📰

An AI-powered news aggregator that scrapes content from YouTube channels and blogs, generates intelligent daily digests using Google Gemini, and delivers them via email.

## Features

- 📺 **YouTube RSS Scraping**: Automatically fetch latest videos from YouTube channels
- 📝 **Blog Content Extraction**: Scrape full blog post content with intelligent parsing
- 🤖 **AI-Powered Summaries**: Generate concise summaries using Google Gemini API
- 📧 **Email Delivery**: Send beautiful HTML digests via Gmail SMTP
- 🗄️ **PostgreSQL Database**: Store and manage sources and articles
- 🐳 **Docker Support**: Self-contained PostgreSQL container
- ⚙️ **Configurable Agent**: Customize digest preferences and focus areas

## Project Structure

```
AI-NEWS-AGGREGATOR/
├── app/
│   ├── scrapers/          # YouTube and blog scrapers
│   ├── llm/               # Gemini API integration
│   ├── email/             # Email sending functionality
│   ├── models.py          # SQLAlchemy database models
│   ├── database.py        # Database configuration
│   └── config.py          # Application configuration
├── agent/
│   ├── system_prompt.txt  # LLM system prompt
│   ├── config.yaml        # Agent preferences
│   └── prompts.py         # Prompt utilities
├── docker/
│   ├── docker-compose.yml # PostgreSQL container
│   └── init.sql           # Database initialization
├── scripts/
│   ├── init_db.py         # Database setup
│   └── add_source.py      # Source management
└── main.py                # Main orchestration script
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Docker Desktop (for PostgreSQL)
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Gmail account with App Password ([Generate here](https://myaccount.google.com/apppasswords))

### 1. Clone and Install Dependencies

```bash
# Navigate to project directory
cd AI-NEWS-AGGREGATOR

# Create virtual environment
uv venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Install dependencies (already done if you followed along)
# Dependencies are already in pyproject.toml
```

### 2. Start PostgreSQL Database

```bash
# Start PostgreSQL container
cd docker
docker-compose up -d

# Verify it's running
docker ps
```

### 3. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and fill in your credentials
```

**Required variables in `.env`:**
```env
# Database (default works with Docker setup)
DATABASE_URL=postgresql://newsaggregator:newspassword@localhost:5432/newsaggregator

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Gmail SMTP
EMAIL_SENDER=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=your.email@gmail.com
```

### 4. Initialize Database

```bash
# Create database tables
python scripts/init_db.py
```

### 5. Add News Sources

```bash
# Run interactive source manager
python scripts/add_source.py
```

**Example sources to add:**

**YouTube Channels:**
- Google DeepMind: `UCUBmRTq9gqz0wgYj4bFXRQA`
- Two Minute Papers: `UCbfYPyITQ-7l4upoX8nvctg`

**Blogs:**
- Google AI Blog RSS: `https://blog.google/technology/ai/rss/`
- OpenAI Blog: `https://openai.com/blog/rss/`

### 6. Test the System

```bash
# Test email configuration
python main.py --mode test-email

# Test scraping
python main.py --mode test-scrape

# Test digest generation
python main.py --mode test-digest
```

### 7. Run Full Workflow

```bash
# Run complete daily digest workflow
python main.py --mode run
```

## Usage

### Running Daily Digest

```bash
python main.py --mode run
```

This will:
1. Scrape all active sources
2. Generate AI summaries with Gemini
3. Send digest email

### CLI Commands

```bash
# Initialize database
python main.py --mode init-db

# Test scraping only
python main.py --mode test-scrape

# Test digest generation only
python main.py --mode test-digest

# Test email sending
python main.py --mode test-email

# Run full workflow
python main.py --mode run
```

### Managing Sources

```bash
# Interactive source management
python scripts/add_source.py
```

Options:
1. Add YouTube channel
2. Add blog
3. List all sources
4. Toggle source active/inactive

## Customizing the Agent

### Edit System Prompt

Edit `agent/system_prompt.txt` to customize:
- Focus areas (AI/ML, specific topics)
- Tone and style
- Technical depth
- Summary guidelines

### Edit Agent Config

Edit `agent/config.yaml` to customize:
- Topics of interest
- Summary length (brief/concise/detailed)
- Model temperature
- Max articles per source

## Deployment to Render

### Option 1: Scheduled Cron Job (Paid Plan)

1. Create new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Add cron job: `0 9 * * * python main.py --mode run`

### Option 2: GitHub Actions (Free)

1. Add secrets to GitHub repository
2. Create `.github/workflows/daily-digest.yml`:

```yaml
name: Daily Digest

on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  run-digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install uv
      - run: uv sync
      - run: python main.py --mode run
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_RECIPIENT: ${{ secrets.EMAIL_RECIPIENT }}
```

## Troubleshooting

### Email Not Sending

- Ensure you're using a Gmail **App Password**, not your regular password
- Generate App Password at: https://myaccount.google.com/apppasswords
- Check that 2-Factor Authentication is enabled on your Google account

### Database Connection Error

- Ensure Docker container is running: `docker ps`
- Check DATABASE_URL in `.env` matches Docker configuration
- Restart container: `docker-compose restart`

### Gemini API Errors

- Verify API key is correct
- Check API quota at: https://makersuite.google.com/app/apikey
- Try switching to `gemini-1.5-pro` if rate limited

### No Articles Found

- Verify sources are active: `python scripts/add_source.py` → Option 3
- Test individual source scraping
- Check source URLs are valid

## Development

### Project Dependencies

- **sqlalchemy**: ORM for database operations
- **psycopg2-binary**: PostgreSQL adapter
- **feedparser**: RSS feed parsing
- **beautifulsoup4** + **lxml**: HTML parsing
- **google-generativeai**: Gemini API client
- **python-dotenv**: Environment variables
- **jinja2**: Email templating
- **pyyaml**: Config file parsing

### Logging

Logs are written to:
- Console (stdout)
- `news_aggregator.log` file

## License

MIT License - feel free to use and modify!

## Contributing

Contributions welcome! Feel free to:
- Add new source types (Reddit, Twitter, etc.)
- Improve content extraction
- Add more LLM providers
- Enhance email templates

---

**Built with ❤️ using Python, PostgreSQL, and Google Gemini**
