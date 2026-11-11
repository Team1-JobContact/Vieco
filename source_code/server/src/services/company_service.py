"""Hồ sơ công ty và quy trình duyệt (FR-M1-13, FR-M1-16, UC-08, BR-02/BR-12).

Vòng đời trạng thái:
    tạo mới -> PENDING --(Admin duyệt)--> APPROVED
                       --(Admin từ chối + lý do)--> REJECTED --(NTD sửa, gửi duyệt lại)--> PENDING
"""
import re
import unicodedata
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.catalog import Industry, Province
from src.models.company import Company, CompanyMember
from src.models.engagement import AuditLog, Notification
from src.models.user import User
from src.schemas.company import (
    AdminCompanyListResponse, AdminCompanyResponse, CompanyCreate, CompanyUpdate, MyCompanyResponse,
)

REQUIRED_FIELDS = ("name", "industry_id", "size", "address", "province_id")
FIELD_LABELS = {"name": "tên công ty", "industry_id": "ngành", "size": "quy mô",
                "address": "địa chỉ", "province_id": "tỉnh/thành"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------- Tiện ích ----------

def slugify(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:200] or "cong-ty"


def _unique_slug(db: Session, name: str) -> str:
    base = slugify(name)
    slug, n = base, 2
    while db.query(Company.id).filter(Company.slug == slug).first():
        slug, n = f"{base}-{n}", n + 1
    return slug


def _check_catalog(db: Session, changes: dict) -> None:
    for key, model, label in (("industry_id", Industry, "Ngành"), ("province_id", Province, "Tỉnh/thành")):
        if changes.get(key) is None:
            continue
        ok = db.query(model.id).filter(model.id == changes[key], model.is_active.is_(True)).first()
        if ok is None:
            raise HTTPException(422, f"{label} không tồn tại")


def _fields(company: Company) -> dict:
    return dict(
        id=company.id, name=company.name, slug=company.slug, logo_url=company.logo_url,
        description=company.description, industry_id=company.industry_id, size=company.size,
        website=company.website, address=company.address, province_id=company.province_id,
        status=company.status, reject_reason=company.reject_reason, reviewed_at=company.reviewed_at,
        created_at=company.created_at, updated_at=company.updated_at,
    )


def _notify_members(db: Session, company: Company, type_: str, title: str, message: str) -> None:
    user_ids = [uid for (uid,) in db.query(CompanyMember.user_id)
                .filter(CompanyMember.company_id == company.id).all()]
    for uid in user_ids:
        db.add(Notification(user_id=uid, type=type_, title=title, message=message,
                            action_url="/employer/company",
                            reference_type="COMPANY", reference_id=company.id))


def _audit(db: Session, user: User, action: str, company: Company, old: dict, new: dict) -> None:
    db.add(AuditLog(user_id=user.id, action=action, entity_type="COMPANY",
                    entity_id=company.id, old_values=old, new_values=new))


# ---------- Nhà tuyển dụng ----------

def find_membership(db: Session, user: User) -> tuple[Company, CompanyMember] | None:
    row = (db.query(Company, CompanyMember)
           .join(CompanyMember, CompanyMember.company_id == Company.id)
           .filter(CompanyMember.user_id == user.id).first())
    return tuple(row) if row else None


def get_membership_or_404(db: Session, user: User) -> tuple[Company, CompanyMember]:
    row = find_membership(db, user)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bạn chưa có hồ sơ công ty")
    return row


def _require_owner(member: CompanyMember) -> None:
    if member.member_role != "OWNER":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ chủ sở hữu công ty mới được thực hiện thao tác này")


def to_my_company(company: Company, member: CompanyMember) -> MyCompanyResponse:
    return MyCompanyResponse(**_fields(company), member_role=member.member_role)


def create_company(db: Session, user: User, data: CompanyCreate) -> MyCompanyResponse:
    if find_membership(db, user) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tài khoản đã gắn với một công ty")
    changes = data.model_dump()
    _check_catalog(db, changes)

    company = Company(**changes, slug=_unique_slug(db, data.name), status="PENDING")
    db.add(company)
    db.flush()
    member = CompanyMember(company_id=company.id, user_id=user.id, member_role="OWNER")
    db.add(member)
    try:
        db.commit()
    except IntegrityError:  # request song song: user đã thành thành viên hoặc trùng slug
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Tài khoản đã gắn với một công ty")
    db.refresh(company)
    db.refresh(member)
    return to_my_company(company, member)


def update_company(db: Session, user: User, data: CompanyUpdate) -> MyCompanyResponse:
    """Sửa hồ sơ. Không tự đổi trạng thái: hồ sơ bị từ chối phải gọi gửi duyệt lại."""
    company, member = get_membership_or_404(db, user)
    _require_owner(member)
    changes = data.model_dump(exclude_unset=True)
    _check_catalog(db, changes)
    for key, value in changes.items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return to_my_company(company, member)


def resubmit_company(db: Session, user: User) -> MyCompanyResponse:
    company, member = get_membership_or_404(db, user)
    _require_owner(member)
    if company.status != "REJECTED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ hồ sơ bị từ chối mới cần gửi duyệt lại")
    missing = [FIELD_LABELS[f] for f in REQUIRED_FIELDS if getattr(company, f) in (None, "")]
    if missing:
        raise HTTPException(422, f"Thiếu thông tin bắt buộc: {', '.join(missing)}")

    company.status = "PENDING"
    company.reject_reason = None  # lý do cũ vẫn còn trong audit_logs
    company.reviewed_by = None
    company.reviewed_at = None
    db.commit()
    db.refresh(company)
    return to_my_company(company, member)


def get_approved_company(db: Session, user: User) -> Company:
    """BR-02/BR-12: dùng cho các API đăng tin ở M2 — chỉ công ty đã duyệt mới được đăng tin."""
    company, _ = get_membership_or_404(db, user)
    if company.status != "APPROVED":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Công ty của bạn chưa được Admin duyệt")
    return company


# ---------- Admin ----------

def _owner_query(db: Session):
    return (db.query(Company, User)
            .outerjoin(CompanyMember, (CompanyMember.company_id == Company.id)
                       & (CompanyMember.member_role == "OWNER"))
            .outerjoin(User, User.id == CompanyMember.user_id))


def _to_admin(company: Company, owner: User | None) -> AdminCompanyResponse:
    return AdminCompanyResponse(
        **_fields(company), reviewed_by=company.reviewed_by,
        owner_id=owner.id if owner else None,
        owner_email=owner.email if owner else None,
        owner_name=owner.full_name if owner else None,
    )


def admin_list_companies(db: Session, status_filter: str | None, keyword: str | None,
                         page: int, page_size: int) -> AdminCompanyListResponse:
    q = _owner_query(db)
    if status_filter:
        q = q.filter(Company.status == status_filter)
    if keyword and keyword.strip():
        like = f"%{keyword.strip()}%"
        q = q.filter(or_(Company.name.ilike(like), User.email.ilike(like)))
    total = q.with_entities(func.count(Company.id)).scalar()
    # Hồ sơ chờ duyệt cũ nhất lên trước để Admin xử lý theo thứ tự
    rows = (q.order_by(Company.created_at.asc() if status_filter == "PENDING" else Company.created_at.desc(),
                       Company.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return AdminCompanyListResponse(items=[_to_admin(c, u) for c, u in rows],
                                    total=total, page=page, page_size=page_size)


def _get_for_admin(db: Session, company_id: int) -> tuple[Company, User | None]:
    row = _owner_query(db).filter(Company.id == company_id).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công ty")
    return row


def admin_get_company(db: Session, company_id: int) -> AdminCompanyResponse:
    return _to_admin(*_get_for_admin(db, company_id))


def _review(db: Session, admin: User, company_id: int, new_status: str,
            reason: str | None) -> AdminCompanyResponse:
    company, owner = _get_for_admin(db, company_id)
    if company.status != "PENDING":
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ duyệt hoặc từ chối hồ sơ đang chờ duyệt")
    old = {"status": company.status}
    company.status = new_status
    company.reject_reason = reason
    company.reviewed_by = admin.id
    company.reviewed_at = _utcnow()

    if new_status == "APPROVED":
        _notify_members(db, company, "COMPANY_APPROVED", "Công ty đã được duyệt",
                        f"Hồ sơ công ty {company.name} đã được duyệt. Bạn có thể bắt đầu đăng tin tuyển dụng.")
        _audit(db, admin, "COMPANY_APPROVE", company, old, {"status": new_status})
    else:
        _notify_members(db, company, "COMPANY_REJECTED", "Hồ sơ công ty bị từ chối",
                        f"Hồ sơ công ty {company.name} bị từ chối. Lý do: {reason}. "
                        "Vui lòng cập nhật thông tin và gửi duyệt lại.")
        _audit(db, admin, "COMPANY_REJECT", company, old, {"status": new_status, "reason": reason})
    db.commit()
    db.refresh(company)
    return _to_admin(company, owner)


def approve_company(db: Session, admin: User, company_id: int) -> AdminCompanyResponse:
    return _review(db, admin, company_id, "APPROVED", None)


def reject_company(db: Session, admin: User, company_id: int, reason: str) -> AdminCompanyResponse:
    return _review(db, admin, company_id, "REJECTED", reason)
