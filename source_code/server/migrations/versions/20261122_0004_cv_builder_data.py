"""Dữ liệu của trình tạo CV trực tuyến, lưu kèm tệp PDF trong mục CV của tôi.

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cvs", sa.Column("builder_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("cvs", "builder_data")
