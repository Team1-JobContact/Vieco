"""Khởi tạo schema nền JobContact (27 bảng, module M0-M3)

Revision ID: 0001
Revises:
Create Date: 2026-11-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


# Hàm hỗ trợ đóng băng trong migration (không import từ src để migration không đổi theo model)
def _id():
    return sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True)


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    ]


def _fk(table, col, target, nullable=False, ondelete=None):
    return sa.Column(
        col, sa.BigInteger(),
        sa.ForeignKey(f"{target}.id", name=f"fk_{table}_{col}_{target}", ondelete=ondelete),
        nullable=nullable,
    )


def _in(table, name, column, values):
    items = ", ".join(f"'{v}'" for v in values)
    return sa.CheckConstraint(f"{column} IN ({items})", name=f"ck_{table}_{name}")


def _pk(table):
    return sa.PrimaryKeyConstraint("id", name=f"pk_{table}")


def _uq(table, *cols, name=None):
    return sa.UniqueConstraint(*cols, name=name or f"uq_{table}_{cols[0]}")


def _bool(name, default):
    return sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.true() if default else sa.false())


def _str_default(name, length, default):
    return sa.Column(name, sa.String(length), nullable=False, server_default=default)


APPLICATION_STATUSES = ("NEW", "VIEWED", "INTERVIEW", "ACCEPTED", "REJECTED", "WITHDRAWN")


def upgrade() -> None:
    # ======================= M0: Danh mục và cấu hình =======================
    op.create_table(
        "industries", _id(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        _bool("is_active", True), *_ts(),
        _pk("industries"), _uq("industries", "name"), _uq("industries", "slug"),
    )

    op.create_table(
        "skills", _id(),
        sa.Column("name", sa.String(100), nullable=False),
        _fk("skills", "industry_id", "industries", nullable=True),
        _bool("is_active", True), *_ts(),
        _pk("skills"), _uq("skills", "name"),
    )

    op.create_table(
        "provinces", _id(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(10), nullable=False),
        _bool("is_active", True), *_ts(),
        _pk("provinces"), _uq("provinces", "name"), _uq("provinces", "code"),
    )

    op.create_table(
        "system_settings", _id(),
        sa.Column("setting_key", sa.String(100), nullable=False),
        sa.Column("setting_value", sa.Text(), nullable=False),
        sa.Column("description", sa.String(255)), *_ts(),
        _pk("system_settings"), _uq("system_settings", "setting_key"),
    )

    op.create_table(
        "static_pages", _id(),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        _bool("is_published", True), *_ts(),
        _pk("static_pages"), _uq("static_pages", "slug"),
    )

    # ======================= M1: Tài khoản và hồ sơ =======================
    op.create_table(
        "roles", _id(),
        sa.Column("name", sa.String(30), nullable=False),
        sa.Column("description", sa.String(255)), *_ts(),
        _pk("roles"), _uq("roles", "name"),
    )

    op.create_table(
        "users", _id(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        _fk("users", "role_id", "roles"),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("avatar_url", sa.String(500)),
        _bool("is_email_verified", False),
        _str_default("status", 20, "ACTIVE"),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime()),
        sa.Column("last_login_at", sa.DateTime()), *_ts(),
        _pk("users"), _uq("users", "email"),
        _in("users", "status", "status", ("ACTIVE", "LOCKED")),
    )

    for table in ("email_verifications", "password_resets"):
        op.create_table(
            table, _id(),
            _fk(table, "user_id", "users", ondelete="CASCADE"),
            sa.Column("token", sa.String(255), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime()), *_ts(),
            _pk(table), _uq(table, "token"),
        )

    op.create_table(
        "candidate_profiles", _id(),
        _fk("candidate_profiles", "user_id", "users", ondelete="CASCADE"),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("gender", sa.String(10)),
        sa.Column("address", sa.String(255)),
        _fk("candidate_profiles", "province_id", "provinces", nullable=True),
        sa.Column("headline", sa.String(150)),
        sa.Column("summary", sa.Text()),
        _str_default("visibility", 10, "PUBLIC"), *_ts(),
        _pk("candidate_profiles"), _uq("candidate_profiles", "user_id"),
        _in("candidate_profiles", "gender", "gender", ("MALE", "FEMALE", "OTHER")),
        _in("candidate_profiles", "visibility", "visibility", ("PUBLIC", "PRIVATE")),
    )

    op.create_table(
        "educations", _id(),
        _fk("educations", "candidate_profile_id", "candidate_profiles", ondelete="CASCADE"),
        sa.Column("school_name", sa.String(200), nullable=False),
        sa.Column("major", sa.String(150)),
        sa.Column("degree", sa.String(50)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("description", sa.Text()), *_ts(),
        _pk("educations"),
    )

    op.create_table(
        "work_experiences", _id(),
        _fk("work_experiences", "candidate_profile_id", "candidate_profiles", ondelete="CASCADE"),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("position", sa.String(150), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("description", sa.Text()), *_ts(),
        _pk("work_experiences"),
    )

    op.create_table(
        "candidate_skills", _id(),
        _fk("candidate_skills", "candidate_profile_id", "candidate_profiles", ondelete="CASCADE"),
        _fk("candidate_skills", "skill_id", "skills"),
        sa.Column("level", sa.String(20)), *_ts(),
        _pk("candidate_skills"),
        _uq("candidate_skills", "candidate_profile_id", "skill_id", name="uq_candidate_skills_profile_skill"),
        _in("candidate_skills", "level", "level", ("BEGINNER", "INTERMEDIATE", "ADVANCED")),
    )

    op.create_table(
        "cvs", _id(),
        _fk("cvs", "candidate_profile_id", "candidate_profiles"),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        _bool("is_default", False),
        sa.Column("deleted_at", sa.DateTime()), *_ts(),
        _pk("cvs"),
    )

    op.create_table(
        "companies", _id(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("description", sa.Text()),
        _fk("companies", "industry_id", "industries", nullable=True),
        sa.Column("size", sa.String(30)),
        sa.Column("website", sa.String(255)),
        sa.Column("address", sa.String(255)),
        _fk("companies", "province_id", "provinces", nullable=True),
        _str_default("status", 20, "PENDING"),
        sa.Column("reject_reason", sa.String(500)),
        _fk("companies", "reviewed_by", "users", nullable=True),
        sa.Column("reviewed_at", sa.DateTime()), *_ts(),
        _pk("companies"), _uq("companies", "slug"),
        _in("companies", "status", "status", ("PENDING", "APPROVED", "REJECTED")),
    )
    op.create_index("ix_companies_status", "companies", ["status"])

    op.create_table(
        "company_members", _id(),
        _fk("company_members", "company_id", "companies"),
        _fk("company_members", "user_id", "users"),
        _str_default("member_role", 20, "MEMBER"), *_ts(),
        _pk("company_members"), _uq("company_members", "user_id"),
        _in("company_members", "member_role", "member_role", ("OWNER", "MEMBER")),
    )

    # ======================= M2: Tuyển dụng và ứng tuyển =======================
    op.create_table(
        "jobs", _id(),
        _fk("jobs", "company_id", "companies"),
        _fk("jobs", "created_by", "users"),
        sa.Column("title", sa.String(200), nullable=False),
        _fk("jobs", "industry_id", "industries", nullable=True),
        _fk("jobs", "province_id", "provinces", nullable=True),
        sa.Column("work_address", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("requirements", sa.Text()),
        sa.Column("benefits", sa.Text()),
        sa.Column("salary_min", sa.BigInteger()),
        sa.Column("salary_max", sa.BigInteger()),
        _str_default("salary_currency", 3, "VND"),
        sa.Column("experience_level", sa.String(30)),
        sa.Column("employment_type", sa.String(20)),
        sa.Column("positions", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("deadline", sa.Date()),
        _str_default("status", 20, "DRAFT"),
        sa.Column("reject_reason", sa.String(500)),
        _fk("jobs", "reviewed_by", "users", nullable=True),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("closed_at", sa.DateTime()),
        _fk("jobs", "removed_by", "users", nullable=True),
        sa.Column("removed_at", sa.DateTime()),
        sa.Column("removal_reason", sa.String(500)),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")), *_ts(),
        _pk("jobs"),
        _in("jobs", "status", "status", ("DRAFT", "PENDING", "APPROVED", "REJECTED", "CLOSED", "EXPIRED")),
        _in("jobs", "employment_type", "employment_type",
            ("FULL_TIME", "PART_TIME", "INTERNSHIP", "CONTRACT", "FREELANCE")),
        _in("jobs", "experience_level", "experience_level",
            ("NONE", "UNDER_1", "FROM_1_TO_3", "FROM_3_TO_5", "OVER_5")),
        sa.CheckConstraint("salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
                           name="ck_jobs_salary_range"),
        sa.CheckConstraint("positions > 0", name="ck_jobs_positions"),
    )
    op.create_index("ix_jobs_status_deadline", "jobs", ["status", "deadline"])
    op.create_index("ix_jobs_company_status", "jobs", ["company_id", "status"])

    op.create_table(
        "job_skills", _id(),
        _fk("job_skills", "job_id", "jobs", ondelete="CASCADE"),
        _fk("job_skills", "skill_id", "skills"), *_ts(),
        _pk("job_skills"), _uq("job_skills", "job_id", "skill_id", name="uq_job_skills_job_skill"),
    )

    op.create_table(
        "applications", _id(),
        _fk("applications", "job_id", "jobs"),
        _fk("applications", "candidate_profile_id", "candidate_profiles"),
        _fk("applications", "cv_id", "cvs"),
        sa.Column("cover_letter", sa.Text()),
        _str_default("status", 20, "NEW"),
        sa.Column("withdrawn_at", sa.DateTime()), *_ts(),
        _pk("applications"),
        _uq("applications", "job_id", "candidate_profile_id", name="uq_applications_job_candidate"),
        _in("applications", "status", "status", APPLICATION_STATUSES),
    )
    op.create_index("ix_applications_job_status", "applications", ["job_id", "status"])

    op.create_table(
        "application_status_history", _id(),
        _fk("application_status_history", "application_id", "applications"),
        sa.Column("from_status", sa.String(20)),
        sa.Column("to_status", sa.String(20), nullable=False),
        _fk("application_status_history", "changed_by", "users"),
        sa.Column("note", sa.String(500)), *_ts(),
        _pk("application_status_history"),
        _in("application_status_history", "from_status", "from_status", APPLICATION_STATUSES),
        _in("application_status_history", "to_status", "to_status", APPLICATION_STATUSES),
    )
    op.create_index("ix_application_status_history_application_created",
                    "application_status_history", ["application_id", "created_at"])

    op.create_table(
        "saved_jobs", _id(),
        _fk("saved_jobs", "candidate_profile_id", "candidate_profiles", ondelete="CASCADE"),
        _fk("saved_jobs", "job_id", "jobs", ondelete="CASCADE"), *_ts(),
        _pk("saved_jobs"), _uq("saved_jobs", "candidate_profile_id", "job_id", name="uq_saved_jobs_candidate_job"),
    )

    # ======================= M3: Thông báo và thống kê =======================
    op.create_table(
        "notifications", _id(),
        _fk("notifications", "user_id", "users"),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_url", sa.String(500)),
        sa.Column("reference_type", sa.String(50)),
        sa.Column("reference_id", sa.BigInteger()),
        _bool("is_read", False),
        sa.Column("read_at", sa.DateTime()),
        _str_default("email_status", 20, "NOT_REQUESTED"),
        sa.Column("email_sent_at", sa.DateTime()), *_ts(),
        _pk("notifications"),
        _in("notifications", "email_status", "email_status", ("NOT_REQUESTED", "PENDING", "SENT", "FAILED")),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read"])

    op.create_table(
        "conversations", _id(),
        _fk("conversations", "application_id", "applications"),
        _fk("conversations", "candidate_user_id", "users"),
        _fk("conversations", "employer_user_id", "users"),
        _str_default("status", 20, "ACTIVE"),
        sa.Column("last_message_at", sa.DateTime()), *_ts(),
        _pk("conversations"), _uq("conversations", "application_id"),
        _in("conversations", "status", "status", ("ACTIVE", "CLOSED")),
    )

    op.create_table(
        "messages", _id(),
        _fk("messages", "conversation_id", "conversations"),
        _fk("messages", "sender_id", "users"),
        sa.Column("content", sa.Text(), nullable=False),
        _bool("is_read", False),
        sa.Column("read_at", sa.DateTime()), *_ts(),
        _pk("messages"),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])

    op.create_table(
        "company_reviews", _id(),
        _fk("company_reviews", "company_id", "companies"),
        _fk("company_reviews", "user_id", "users"),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        _str_default("status", 20, "PENDING"),
        _fk("company_reviews", "reviewed_by", "users", nullable=True),
        sa.Column("reviewed_at", sa.DateTime()), *_ts(),
        _pk("company_reviews"),
        _uq("company_reviews", "company_id", "user_id", name="uq_company_reviews_company_user"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_company_reviews_rating"),
        _in("company_reviews", "status", "status", ("PENDING", "APPROVED", "REJECTED")),
    )

    op.create_table(
        "reports", _id(),
        _fk("reports", "reporter_id", "users"),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        _str_default("status", 20, "PENDING"),
        _fk("reports", "reviewed_by", "users", nullable=True),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("resolution_note", sa.Text()), *_ts(),
        _pk("reports"),
        _in("reports", "target_type", "target_type", ("JOB", "USER", "COMPANY")),
        _in("reports", "status", "status", ("PENDING", "CONFIRMED", "DISMISSED", "ACTION_TAKEN")),
    )
    op.create_index("ix_reports_target", "reports", ["target_type", "target_id"])
    op.create_index("ix_reports_status", "reports", ["status"])

    op.create_table(
        "audit_logs", _id(),
        _fk("audit_logs", "user_id", "users", nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.BigInteger()),
        sa.Column("old_values", sa.JSON()),
        sa.Column("new_values", sa.JSON()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)), *_ts(),
        _pk("audit_logs"),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_user_created", "audit_logs", ["user_id", "created_at"])


def downgrade() -> None:
    # Xóa theo thứ tự ngược chiều phụ thuộc: M3 -> M2 -> M1 -> M0
    for table in (
        "audit_logs", "reports", "company_reviews", "messages", "conversations", "notifications",
        "saved_jobs", "application_status_history", "applications", "job_skills", "jobs",
        "company_members", "companies", "cvs", "candidate_skills", "work_experiences", "educations",
        "candidate_profiles", "password_resets", "email_verifications", "users", "roles",
        "static_pages", "system_settings", "provinces", "skills", "industries",
    ):
        op.drop_table(table)
