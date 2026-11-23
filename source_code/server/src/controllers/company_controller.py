from fastapi import Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.company import (
    AdminCompanyListResponse, AdminCompanyResponse, CompanyCreate, CompanyStatus,
    CompanyUpdate, MyCompanyResponse, RejectRequest, VerificationRequest,
)
from src.services import company_media_service, company_service

# ---------- Nhà tuyển dụng: hồ sơ công ty của mình ----------

employer_only = require_roles("EMPLOYER")


def get_my_company(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    """Xem hồ sơ công ty, trạng thái duyệt và lý do từ chối (nếu có)."""
    return company_service.to_my_company(*company_service.get_membership_or_404(db, user))


def create_my_company(data: CompanyCreate, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    """Tạo hồ sơ công ty; người tạo là OWNER; trạng thái mặc định PENDING (chờ duyệt)."""
    return company_service.create_company(db, user, data)


def update_my_company(data: CompanyUpdate, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_service.update_company(db, user, data)


def resubmit_my_company(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    """Gửi duyệt lại hồ sơ đã bị từ chối (REJECTED -> PENDING)."""
    return company_service.resubmit_company(db, user)


# ---------- Admin: duyệt công ty ----------

admin_only = require_roles("ADMIN")


def list_companies(
    status_filter: CompanyStatus | None = Query(None, alias="status"),
    q: str | None = Query(None, max_length=100, description="Tìm theo tên công ty hoặc email chủ sở hữu"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    return company_service.admin_list_companies(db, status_filter, q, page, page_size)


def get_company(company_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    return company_service.admin_get_company(db, company_id)


def approve_company(company_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    return company_service.approve_company(db, admin, company_id)


def reject_company(company_id: int, data: RejectRequest, admin: User = Depends(admin_only),
                   db: Session = Depends(get_db)):
    return company_service.reject_company(db, admin, company_id, data.reason)


def verify_company(company_id: int, data: VerificationRequest, admin: User = Depends(admin_only),
                   db: Session = Depends(get_db)):
    """Bật/tắt dấu tick vàng "Doanh nghiệp đã xác minh"."""
    return company_service.set_verified(db, admin, company_id, data.verified)


# ---------- Hình ảnh công ty: logo, ảnh bìa, ảnh không gian làm việc ----------

def get_my_media(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    """Xem hình ảnh hiện có của công ty mình và giới hạn tải lên."""
    return company_media_service.get_media(db, user)


def upload_logo(file: UploadFile = File(...), user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_media_service.set_logo(db, user, file)


def delete_logo(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_media_service.delete_logo(db, user)


def upload_cover(file: UploadFile = File(...), user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_media_service.set_cover(db, user, file)


def delete_cover(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_media_service.delete_cover(db, user)


def upload_image(file: UploadFile = File(...), user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_media_service.add_image(db, user, file)


def delete_image(image_id: int, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_media_service.delete_image(db, user, image_id)


def serve_company_media(file_name: str):
    """Ảnh công ty là nội dung công khai; không cần đăng nhập."""
    path, media_type = company_media_service.file_for_serving(file_name)
    return FileResponse(path, media_type=media_type,
                        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=86400"})
