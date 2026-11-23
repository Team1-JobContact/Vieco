"""Xác minh doanh nghiệp: Admin gắn dấu tick vàng cho công ty đã duyệt.

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("companies", sa.Column("verified_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "verified_at")
    op.drop_column("companies", "is_verified")
