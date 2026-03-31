"""initial schema

Revision ID: 9c615cf7ecec
Revises:
Create Date: 2026-03-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9c615cf7ecec"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension exists before creating vector columns
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("youtube", "openai", "anthropic", "blog", name="sourcetype"),
            nullable=False,
        ),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_sources_id", "sources", ["id"])

    # --- articles ---
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("video_id", sa.String(128), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("full_content", sa.Text(), nullable=True),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_articles_id", "articles", ["id"])
    op.create_index("ix_articles_url", "articles", ["url"])
    op.create_index("ix_articles_source_id", "articles", ["source_id"])
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_scraped_at", "articles", ["scraped_at"])
    op.create_index("ix_articles_processing_status", "articles", ["processing_status"])

    # --- openai_articles (legacy) ---
    op.create_table(
        "openai_articles",
        sa.Column("guid", sa.String(512), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("guid"),
    )
    op.create_index("ix_openai_articles_guid", "openai_articles", ["guid"])

    # --- anthropic_articles (legacy) ---
    op.create_table(
        "anthropic_articles",
        sa.Column("guid", sa.String(512), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("guid"),
    )
    op.create_index("ix_anthropic_articles_guid", "anthropic_articles", ["guid"])

    # --- youtube_videos (legacy) ---
    op.create_table(
        "youtube_videos",
        sa.Column("guid", sa.String(512), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("guid"),
    )
    op.create_index("ix_youtube_videos_guid", "youtube_videos", ["guid"])

    # --- article_summaries ---
    op.create_table(
        "article_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_points", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_article_summaries_id", "article_summaries", ["id"])
    op.create_index("ix_article_summaries_article_id", "article_summaries", ["article_id"])

    # --- article_embeddings ---
    # Create as TEXT first, then cast to vector(384) after pgvector is enabled
    op.create_table(
        "article_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("model", sa.String(50), nullable=False, server_default="all-MiniLM-L6-v2"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id"),
    )
    op.create_index("ix_article_embeddings_id", "article_embeddings", ["id"])
    op.create_index("ix_article_embeddings_article_id", "article_embeddings", ["article_id"])
    op.execute(
        "ALTER TABLE article_embeddings ALTER COLUMN embedding TYPE vector(384) "
        "USING embedding::vector(384)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_embedding_vector "
        "ON article_embeddings USING ivfflat (embedding vector_cosine_ops)"
    )

    # --- email_subscriptions ---
    op.create_table(
        "email_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column(
            "frequency",
            sa.Enum("daily", "weekly", "custom", name="emailfrequency"),
            nullable=False,
        ),
        sa.Column("source_filters", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_email_subscriptions_id", "email_subscriptions", ["id"])
    op.create_index("ix_email_subscriptions_email", "email_subscriptions", ["email"])
    op.create_index("ix_email_subscriptions_is_active", "email_subscriptions", ["is_active"])

    # --- email_deliveries ---
    op.create_table(
        "email_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "sent", "failed", "bounced", name="deliverystatus"),
            nullable=False,
        ),
        sa.Column("articles_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles_ids", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["subscription_id"], ["email_subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_deliveries_id", "email_deliveries", ["id"])
    op.create_index("ix_email_deliveries_subscription_id", "email_deliveries", ["subscription_id"])

    # --- processing_queue ---
    op.create_table(
        "processing_queue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "extracting", "summarizing", "embedding", "completed", "failed",
                name="processingstatus",
            ),
            nullable=False,
        ),
        sa.Column("current_stage", sa.String(50), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processing_queue_id", "processing_queue", ["id"])
    op.create_index("ix_processing_queue_article_id", "processing_queue", ["article_id"])
    op.create_index("ix_processing_queue_status", "processing_queue", ["status"])


def downgrade() -> None:
    op.drop_table("processing_queue")
    op.drop_table("email_deliveries")
    op.drop_table("email_subscriptions")
    op.drop_table("article_embeddings")
    op.drop_table("article_summaries")
    op.drop_table("youtube_videos")
    op.drop_table("anthropic_articles")
    op.drop_table("openai_articles")
    op.drop_table("articles")
    op.drop_table("sources")
    op.execute("DROP TYPE IF EXISTS processingstatus")
    op.execute("DROP TYPE IF EXISTS deliverystatus")
    op.execute("DROP TYPE IF EXISTS emailfrequency")
    op.execute("DROP TYPE IF EXISTS sourcetype")
