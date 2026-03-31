"""add pipeline_runs table

Revision ID: e35de033c420
Revises: b850dc962822
Create Date: 2026-03-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e35de033c420"
down_revision: Union[str, None] = "b850dc962822"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("articles_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pipeline_runs_id", "pipeline_runs", ["id"])
    op.create_index("ix_pipeline_runs_started_at", "pipeline_runs", ["started_at"])


def downgrade() -> None:
    op.drop_table("pipeline_runs")
