from typing import Literal

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.admin import CategoryUpdate, PageUpdate, UploadSettingUpdate, UserStatusUpdate
from src.services import admin_service

admin = require_roles("ADMIN")


def list_users(q: str | None = Query(None, max_length=100),
               role: Literal["ADMIN", "CANDIDATE", "EMPLOYER"] | None = None,
               status: Literal["ACTIVE", "LOCKED"] | None = None,
               page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               _: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.list_users(db, q, role, status, page, page_size)


def user_detail(user_id: int, _: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.user_detail(db, user_id)


def update_user_status(user_id: int, data: UserStatusUpdate, user: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.update_user_status(db, user, user_id, data.status)


def list_categories(_: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.list_categories(db)


def update_category(kind: Literal["industries", "skills", "provinces"], category_id: int,
                    data: CategoryUpdate, user: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.update_category(db, user, kind, category_id, data)


def list_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                    _: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.list_audit_logs(db, page, page_size)


def list_pages(_: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.list_pages(db)


def update_page(page_id: int, data: PageUpdate, user: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.update_page(db, user, page_id, data)


def public_page(slug: str, db: Session = Depends(get_db)):
    return admin_service.public_page(db, slug)


def list_upload_settings(_: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.list_upload_settings(db)


def update_upload_setting(key: str, data: UploadSettingUpdate, user: User = Depends(admin), db: Session = Depends(get_db)):
    return admin_service.update_upload_setting(db, user, key, data.value)
