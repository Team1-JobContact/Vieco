"""Module M3: Thông báo, nhắn tin, đánh giá, báo cáo vi phạm, nhật ký hoạt động."""
from sqlalchemy import (
    JSON, CheckConstraint, Column, DateTime, Index, SmallInteger, String, Text, UniqueConstraint,
)
from src.models.base import BaseModel, BigInt, fk, flag, in_check
from src.models.enums import (
    CONVERSATION_STATUSES, EMAIL_STATUSES, REPORT_STATUSES, REPORT_TARGET_TYPES, REVIEW_STATUSES,
)


class Notification(BaseModel):
    __tablename__ = "notifications"
    __table_args__ = (
        in_check("email_status", EMAIL_STATUSES, "email_status"),
        Index("ix_notifications_user_read", "user_id", "is_read"),
    )

    user_id = fk("users.id")
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500))
    reference_type = Column(String(50))
    reference_id = Column(BigInt)
    is_read = flag(False)
    read_at = Column(DateTime)
    email_status = Column(String(20), nullable=False, default="NOT_REQUESTED", server_default="NOT_REQUESTED")
    email_sent_at = Column(DateTime)


class Conversation(BaseModel):
    __tablename__ = "conversations"
    __table_args__ = (in_check("status", CONVERSATION_STATUSES, "status"),)

    application_id = fk("applications.id", unique=True)   # chỉ nhắn tin khi đã có đơn (FR-M3-06)
    candidate_user_id = fk("users.id")
    employer_user_id = fk("users.id")
    status = Column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    last_message_at = Column(DateTime)


class Message(BaseModel):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)

    conversation_id = fk("conversations.id")
    sender_id = fk("users.id")
    content = Column(Text, nullable=False)
    is_read = flag(False)
    read_at = Column(DateTime)


class CompanyReview(BaseModel):
    __tablename__ = "company_reviews"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_company_reviews_company_user"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating"),
        in_check("status", REVIEW_STATUSES, "status"),
    )

    company_id = fk("companies.id")
    user_id = fk("users.id")
    rating = Column(SmallInteger, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    reviewed_by = fk("users.id", nullable=True)
    reviewed_at = Column(DateTime)


class Report(BaseModel):
    __tablename__ = "reports"
    __table_args__ = (
        in_check("target_type", REPORT_TARGET_TYPES, "target_type"),
        in_check("status", REPORT_STATUSES, "status"),
        Index("ix_reports_target", "target_type", "target_id"),
        Index("ix_reports_status", "status"),
    )

    reporter_id = fk("users.id")
    target_type = Column(String(30), nullable=False)
    target_id = Column(BigInt, nullable=False)
    reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    reviewed_by = fk("users.id", nullable=True)
    reviewed_at = Column(DateTime)
    resolution_note = Column(Text)


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
    )

    user_id = fk("users.id", nullable=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(BigInt)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
