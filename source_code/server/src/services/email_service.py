import hashlib
import logging
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from fastapi import HTTPException
from src.config import mailer
from src.config.settings import settings
from src.models.user import EmailVerification, PasswordReset, User
from src.services.auth_service import _utcnow
from src.utils.security import hash_password

logger = logging.getLogger(__name__)

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def _deliver(email, kind, raw):
    link = settings.FRONTEND_URL.rstrip("/") + "/pages/account.html?" + urlencode({"action": kind, "token": raw})
    subject = "Xác thực tài khoản" if kind == "verify-email" else "Đặt lại mật khẩu"
    try:
        mailer.send_email(email, subject, f"{subject} JobContact: {link}\nLiên kết chỉ dùng một lần.")
    except Exception:
        # Transport exceptions can include recipient details; don't log their content.
        logger.error("SMTP delivery failed")
        raise HTTPException(503, "Chưa gửi được email, vui lòng thử lại sau")

def issue_verification(db, user):
    if not settings.SMTP_HOST:
        return
    raw = secrets.token_urlsafe(32)
    db.add(EmailVerification(user_id=user.id, token=digest(raw), expires_at=_utcnow()+timedelta(hours=24)))
    db.commit()
    return raw

def verify_email(db, token):
    now = _utcnow()
    row = db.query(EmailVerification).filter(EmailVerification.token == digest(token)).with_for_update().first()
    if row is None or row.used_at is not None or row.expires_at <= now:
        raise HTTPException(400, "Token không hợp lệ hoặc đã hết hạn")
    user = db.get(User, row.user_id)
    user.is_email_verified = True
    row.used_at = now
    db.commit()
    return {"message": "Xác thực email thành công"}

def forgot_password(db, email):
    if not settings.SMTP_HOST:
        raise HTTPException(503, "Chưa cấu hình SMTP")
    user = db.query(User).filter(User.email == email.lower(), User.status == "ACTIVE").first()
    if user:
        now = _utcnow()
        # Supersede previous unused reset links.
        db.query(PasswordReset).filter(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None)).update({"expires_at": now})
        raw = secrets.token_urlsafe(32)
        db.add(PasswordReset(user_id=user.id, token=digest(raw), expires_at=now+timedelta(minutes=30)))
        db.commit()
        _deliver(user.email, "reset-password", raw)
    return {"message": "Nếu tài khoản tồn tại, email đặt lại mật khẩu sẽ được gửi"}

def reset_password(db, data):
    now = _utcnow()
    row = db.query(PasswordReset).filter(PasswordReset.token == digest(data.token)).with_for_update().first()
    if row is None or row.used_at is not None or row.expires_at <= now:
        raise HTTPException(400, "Token không hợp lệ hoặc đã hết hạn")
    user = db.get(User, row.user_id)
    user.password_hash = hash_password(data.password)
    user.failed_login_count = 0
    user.locked_until = None
    row.used_at = now
    db.query(PasswordReset).filter(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None), PasswordReset.id != row.id).update({"expires_at": now})
    db.commit()
    return {"message": "Đặt lại mật khẩu thành công"}
