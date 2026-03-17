"""create watchlist and raw_events tables

Revision ID: 0001
Revises:
Create Date: 2026-03-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    watchlist_table = op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("cik", sa.String(10), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "raw_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("form_type", sa.String(), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("accession_number", sa.String(), nullable=False),
        sa.Column("primary_document", sa.String(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("dedupe_key", sa.String(), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("processed", sa.String(), nullable=False, server_default="NO"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key", name="uq_raw_events_dedupe_key"),
    )

    # Seed the two required watchlist rows
    op.bulk_insert(
        watchlist_table,
        [
            {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "cik": "0000320193",
                "active": True,
            },
            {
                "ticker": "MSFT",
                "company_name": "Microsoft Corp.",
                "cik": "0000789019",
                "active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("raw_events")
    op.drop_table("watchlist")
