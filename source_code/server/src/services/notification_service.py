from fastapi import HTTPException
from src.models.engagement import Notification
from src.services.auth_service import _utcnow

def fields(row):
    return {key: getattr(row,key) for key in ("id","type","title","message","action_url","is_read","read_at","created_at")}

def list_notifications(db,user,page,page_size):
    query = db.query(Notification).filter(Notification.user_id == user.id)
    total = query.count()
    rows = query.order_by(Notification.created_at.desc(), Notification.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return dict(items=[fields(r) for r in rows], total=total, page=page, page_size=page_size)

def mark_read(db,user,notification_id):
    row = db.query(Notification).filter(Notification.id == notification_id,Notification.user_id == user.id).first()
    if row is None:
        raise HTTPException(404,"Không tìm thấy thông báo")
    if not row.is_read:
        row.is_read = True
        row.read_at = _utcnow()
        db.commit()
    return fields(row)


def send_for_reference(db, reference_type, reference_id):
    """Best effort SMTP after the business transaction commits; record delivery state."""
    import logging
    from src.config.settings import settings
    from src.config import mailer
    from src.models.user import User
    if not settings.SMTP_HOST:
        return
    rows = db.query(Notification).filter(
        Notification.reference_type == reference_type,
        Notification.reference_id == reference_id,
        Notification.email_status == "NOT_REQUESTED",
    ).all()
    for row in rows:
        user = db.get(User, row.user_id)
        try:
            mailer.send_email(user.email, row.title, row.message)
        except Exception:
            row.email_status = "FAILED"
            logging.getLogger(__name__).error("Notification email delivery failed")
        else:
            row.email_status = "SENT"
            row.email_sent_at = _utcnow()
    if rows:
        db.commit()
