from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.company import (
    AdminCompanyListResponse, AdminCompanyResponse, CompanyCreate, CompanyStatus,
    CompanyUpdate, MyCompanyResponse, RejectRequest,
)
from src.services import company_service

# ---------- Nhà tuyển dụng: hồ sơ công ty của mình ----------

employer_router = APIRouter(prefix="/api/v1/employer/company", tags=["Employer Company"])
employer_only = require_roles("EMPLOYER")


@employer_router.get("", response_model=MyCompanyResponse)
def get_my_company(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    """Xem hồ sơ công ty, trạng thái duyệt và lý do từ chối (nếu có)."""
    return company_service.to_my_company(*company_service.get_membership_or_404(db, user))


@employer_router.post("", response_model=MyCompanyResponse, status_code=status.HTTP_201_CREATED)
def create_my_company(data: CompanyCreate, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    """Tạo hồ sơ công ty; người tạo là OWNER; trạng thái mặc định PENDING (chờ duyệt)."""
    return company_service.create_company(db, user, data)


@employer_router.patch("", response_model=MyCompanyResponse)
def update_my_company(data: CompanyUpdate, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return company_service.update_company(db, user, data)


@employer_router.post("/resubmit", response_model=MyCompanyResponse)
def resubmit_my_company(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    """Gửi duyệt lại hồ sơ đã bị từ chối (REJECTED -> PENDING)."""
    return company_service.resubmit_company(db, user)


# ---------- Admin: duyệt công ty ----------

admin_router = APIRouter(prefix="/api/v1/admin/companies", tags=["Admin Company"])
admin_only = require_roles("ADMIN")


@admin_router.get("", response_model=AdminCompanyListResponse)
def list_companies(
    status_filter: CompanyStatus | None = Query(None, alias="status"),
    q: str | None = Query(None, max_length=100, description="Tìm theo tên công ty hoặc email chủ sở hữu"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    return company_service.admin_list_companies(db, status_filter, q, page, page_size)


@admin_router.get("/{company_id}", response_model=AdminCompanyResponse)
def get_company(company_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    return company_service.admin_get_company(db, company_id)


@admin_router.post("/{company_id}/approve", response_model=AdminCompanyResponse)
def approve_company(company_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    return company_service.approve_company(db, admin, company_id)


@admin_router.post("/{company_id}/reject", response_model=AdminCompanyResponse)
def reject_company(company_id: int, data: RejectRequest, admin: User = Depends(admin_only),
                   db: Session = Depends(get_db)):
    return company_service.reject_company(db, admin, company_id, data.reason)
