"""add dead_letters table

Revision ID: b850dc962822
Revises: 9c615cf7ecec
Create Date: 2026-03-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b850dc962822"
down_revision: Union[str, None] = "9c615cf7ecec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dead_letters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("queue_name", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("replayed_at", sa.DateTime(), nullable=True),
        sa.Column("replayed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dead_letters_id", "dead_letters", ["id"])
    op.create_index("ix_dead_letters_article_id", "dead_letters", ["article_id"])
    op.create_index("ix_dead_letters_failed_at", "dead_letters", ["failed_at"])


def downgrade() -> None:
    op.drop_table("dead_letters")
