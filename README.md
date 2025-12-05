# NexusFeed: Production-Grade AI News Aggregation Pipeline
*Not a tutorial project. A multi-source ingestion system with LLM-powered summarization and automated delivery.*

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 **The 10-Second Pitch**
Most AI news aggregators are glorified RSS readers. This is a **production-ready ingestion pipeline** that:
- Processes 1,000+ articles daily from **YouTube, blogs, and RSS feeds**
- Generates **context-aware summaries** using Google Gemini (with Claude/OpenAI fallback)
- Delivers **personalized digests** via automated email campaigns
- Manages **stateful processing** with PostgreSQL and Redis
- Is **deployable today** on Render/Vercel with scheduled cron jobs

## 🚨 **What Makes This Different (Recruiter Edition)**

| Typical Project | This Project |
|----------------|--------------|
| Uses public RSS feeds | **Multi-source ingestion** (YouTube API + RSS + web scraping) |
| Single LLM call per article | **Pipeline architecture** with caching, retries, fallbacks |
| CLI script | **Containerized services** with proper error handling |
| "Email sending" | **Transactional email system** with templates and tracking |
| Local SQLite | **PostgreSQL with connection pooling** |

## 📊 **Architecture: The Technical Depth That Matters**

```mermaid
graph TB
    subgraph "Ingestion Layer"
        A[YouTube API] --> E[Message Queue]
        B[RSS Feeds] --> E
        C[Web Scrapers] --> E
    end
    
    subgraph "Processing Pipeline"
        E --> F{Orchestrator}
        F --> G[Content Extraction]
        G --> H[LLM Summarization<br/>Gemini/Claude/Llama]
        H --> I[Vector Embeddings]
    end
    
    subgraph "Delivery & State"
        I --> J[PostgreSQL<br/>with Article Metadata]
        I --> K[Redis Cache<br/>for API responses]
        J --> L[Email Engine<br/>Jinja2 Templates]
        L --> M[SMTP/Resend API]
    end
    
    style H fill:#ff6b6b
    style J fill:#4ecdc4