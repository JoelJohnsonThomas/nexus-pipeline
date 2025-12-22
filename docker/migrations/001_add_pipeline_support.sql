-- Migration: Add pgvector extension and new pipeline tables
-- This script extends the database schema for the AI News Aggregator pipeline

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Add new columns to articles table for pipeline processing
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending' NOT NULL,
ADD COLUMN IF NOT EXISTS full_content TEXT,
ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50);

-- Create index on processing_status for efficient filtering
CREATE INDEX IF NOT EXISTS idx_articles_processing_status ON articles(processing_status);

-- Note: The other tables (article_summaries, article_embeddings, email_subscriptions, etc.)
-- will be created automatically by SQLAlchemy's Base.metadata.create_all() when the app runs
-- This migration only adds essential extensions and columns to existing tables

SELECT 'Migration completed: pgvector enabled and articles table updated' AS status;
