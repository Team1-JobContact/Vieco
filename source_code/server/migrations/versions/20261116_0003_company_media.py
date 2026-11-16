"""Ảnh công ty do nhà tuyển dụng tự tải lên: ảnh bìa và ảnh không gian làm việc.

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("cover_url", sa.String(500), nullable=True))
    op.create_table(
        "company_images",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_company_images"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE",
                                name="fk_company_images_company_id_companies"),
    )
    op.create_index("ix_company_images_company_id", "company_images", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_company_images_company_id", table_name="company_images")
    op.drop_table("company_images")
    op.drop_column("companies", "cover_url")
