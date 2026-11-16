from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from src.models.catalog import StaticPage, SystemSetting
from src.models.engagement import AuditLog
from src.models.user import Role, User
from src.services.auth_service import to_user_response
from src.services.catalog_service import MODELS


def list_users(db, q, role, status, page, page_size):
    query = db.query(User, Role.name).join(Role, Role.id == User.role_id)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    if role:
        query = query.filter(Role.name == role)
    if status:
        query = query.filter(User.status == status)
    total = query.count()
    rows = query.order_by(User.created_at.desc(), User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return dict(items=[to_user_response(user, name) for user, name in rows], total=total,
                page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


def user_detail(db, user_id):
    row = db.query(User, Role.name).join(Role, Role.id == User.role_id).filter(User.id == user_id).first()
    if row is None:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    user, role = row
    return dict(**to_user_response(user, role).model_dump(), last_login_at=user.last_login_at,
                failed_login_count=user.failed_login_count, locked_until=user.locked_until)


def audit(db, actor, action, entity_type, entity_id, old, new):
    db.add(AuditLog(user_id=actor.id, action=action, entity_type=entity_type,
                    entity_id=entity_id, old_values=old, new_values=new))


def update_user_status(db, actor, user_id, status):
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if user is None:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    old = {"status": user.status}
    user.status = status
    if status == "ACTIVE":
        user.failed_login_count = 0
        user.locked_until = None
    audit(db, actor, "USER_STATUS", "USER", user.id, old, {"status": status})
    db.commit()
    return user_detail(db, user.id)


def category_fields(kind, row):
    keys = ["id", "name", "is_active"]
    keys += {"industries": ["slug"], "skills": ["industry_id"], "provinces": ["code"]}[kind]
    return {key: getattr(row, key) for key in keys}


def list_categories(db):
    return {kind: [category_fields(kind, row) for row in db.query(model).order_by(model.name, model.id)]
            for kind, model in MODELS.items()}


def update_category(db, actor, kind, category_id, data):
    if data.type != kind:
        raise HTTPException(422, "Loại danh mục không khớp đường dẫn")
    model = MODELS[kind]
    row = db.query(model).filter(model.id == category_id).with_for_update().first()
    if row is None:
        raise HTTPException(404, "Không tìm thấy danh mục")
    if kind == "skills" and data.industry_id is not None:
        industry = db.get(MODELS["industries"], data.industry_id)
        if industry is None or (not industry.is_active and row.industry_id != data.industry_id):
            raise HTTPException(422, "Ngành nghề không tồn tại hoặc đã bị ẩn")
    old = category_fields(kind, row)
    row.name = data.name
    row.is_active = data.is_active
    if kind == "provinces":
        row.code = data.code
    if kind == "skills":
        row.industry_id = data.industry_id
    audit(db, actor, "CATEGORY_UPDATE", kind.upper(), row.id, old, category_fields(kind, row))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Tên hoặc mã danh mục đã tồn tại")
    return category_fields(kind, row)


def list_audit_logs(db, page, page_size):
    query = db.query(AuditLog, User.full_name).outerjoin(User, User.id == AuditLog.user_id)
    total = query.count()
    rows = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return dict(items=[dict(id=row.id, actor_name=name, action=row.action, entity_type=row.entity_type,
                            entity_id=row.entity_id, old_values=row.old_values, new_values=row.new_values,
                            created_at=row.created_at) for row, name in rows],
                total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


def page_fields(row):
    return {key: getattr(row, key) for key in ("id", "slug", "title", "content", "is_published")}


def list_pages(db):
    return [page_fields(row) for row in db.query(StaticPage).order_by(StaticPage.id)]


def update_page(db, actor, page_id, data):
    row = db.get(StaticPage, page_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy trang")
    old = page_fields(row)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    audit(db, actor, "PAGE_UPDATE", "STATIC_PAGE", row.id, old, page_fields(row))
    db.commit()
    return page_fields(row)


def public_page(db, slug):
    row = db.query(StaticPage).filter(StaticPage.slug == slug, StaticPage.is_published.is_(True)).first()
    if row is None:
        raise HTTPException(404, "Trang không tồn tại hoặc chưa được xuất bản")
    return dict(slug=row.slug, title=row.title, content=row.content)


UPLOAD_SETTINGS = {
    "cv_max_size_mb": ("Dung lượng tối đa mỗi CV (MB)", "5"),
    "cv_max_count": ("Số CV tối đa mỗi hồ sơ", "5"),
    "cv_allowed_extensions": ("Định dạng CV (cách nhau bằng dấu phẩy)", "pdf,doc,docx"),
    "image_max_size_mb": ("Dung lượng logo tối đa (MB)", "2"),
}


def list_upload_settings(db):
    rows = dict(db.query(SystemSetting.setting_key, SystemSetting.setting_value).filter(
        SystemSetting.setting_key.in_(UPLOAD_SETTINGS)).all())
    return [dict(key=key, label=label, value=rows.get(key, default))
            for key, (label, default) in UPLOAD_SETTINGS.items()]


def update_upload_setting(db, actor, key, value):
    if key not in UPLOAD_SETTINGS:
        raise HTTPException(404, "Không tìm thấy cấu hình tải tệp")
    if key == "cv_allowed_extensions":
        extensions = list(dict.fromkeys(part.strip().lower().lstrip(".") for part in value.split(",")))
        if not extensions or not set(extensions).issubset({"pdf", "doc", "docx"}):
            raise HTTPException(422, "Chỉ chấp nhận pdf, doc, docx")
        value = ",".join(extensions)
    else:
        if not value.isascii() or not value.isdigit() or int(value) < 1:
            raise HTTPException(422, "Giá trị phải là số nguyên lớn hơn 0")
        value = str(int(value))
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == key).with_for_update().first()
    old = {"value": row.setting_value if row else UPLOAD_SETTINGS[key][1]}
    if row is None:
        row = SystemSetting(setting_key=key, description=UPLOAD_SETTINGS[key][0])
        db.add(row)
    row.setting_value = value
    try:
        db.flush()
        audit(db, actor, "SETTING_UPDATE", "SYSTEM_SETTING", row.id, old, {"value": value})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Cấu hình vừa thay đổi, vui lòng tải lại và thử lại")
    return dict(key=key, value=value)
