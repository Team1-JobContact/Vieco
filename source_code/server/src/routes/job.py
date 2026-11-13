from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.job import (
    JobCreate, JobExtendRequest, JobListResponse, JobRejectRequest,
    JobRemoveRequest, JobResponse, JobStatus, JobUpdate,
)
from src.services import job_service

# ---------- Nhà tuyển dụng: Quản lý tin tuyển dụng (FR-M2-01..05, BR-02, BR-04) ----------

employer_router = APIRouter(prefix="/api/v1/employer/jobs", tags=["Employer Jobs"])
employer_only = require_roles("EMPLOYER")


@employer_router.get("", response_model=JobListResponse)
def list_my_jobs(
    status_filter: JobStatus | None = Query(None, alias="status", description="Lọc theo trạng thái tin"),
    q: str | None = Query(None, max_length=100, description="Tìm kiếm theo tiêu đề tin tuyển dụng"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Xem danh sách tin tuyển dụng thuộc công ty của mình (có phân trang và lọc)."""
    return job_service.list_employer_jobs(db, user, status_filter, q, page, page_size)


@employer_router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Tạo tin tuyển dụng: có thể lưu nháp (action='draft') hoặc gửi duyệt ngay (action='submit').
    Yêu cầu công ty đã được Admin duyệt (BR-02, BR-12)."""
    return job_service.create_job(db, user, data)


@employer_router.get("/{job_id}", response_model=JobResponse)
def get_my_job(
    job_id: int,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Xem chi tiết một tin tuyển dụng của công ty mình."""
    return job_service.get_employer_job(db, user, job_id)


@employer_router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    data: JobUpdate,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Chỉnh sửa tin tuyển dụng.
    Lưu ý: Tin đã duyệt (APPROVED) nếu sửa đổi nội dung chính sẽ tự động chuyển về PENDING để duyệt lại (FR-M2-03)."""
    return job_service.update_job(db, user, job_id, data)


@employer_router.post("/{job_id}/submit", response_model=JobResponse)
def submit_job(
    job_id: int,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Gửi duyệt tin nháp hoặc tin đã bị từ chối (DRAFT/REJECTED -> PENDING) (BR-04, BR-14)."""
    return job_service.submit_job(db, user, job_id)


@employer_router.post("/{job_id}/close", response_model=JobResponse)
def close_job(
    job_id: int,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Đóng tin tuyển dụng đang mở (APPROVED -> CLOSED) (FR-M2-04)."""
    return job_service.close_job(db, user, job_id)


@employer_router.post("/{job_id}/reopen", response_model=JobResponse)
def reopen_job(
    job_id: int,
    new_deadline: date | None = Query(None, description="Hạn nộp mới nếu hạn nộp cũ đã qua"),
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Mở lại tin tuyển dụng đã đóng (CLOSED -> PENDING để duyệt lại) (FR-M2-04, Bảng 3.7.1)."""
    return job_service.reopen_job(db, user, job_id, new_deadline)


@employer_router.post("/{job_id}/extend", response_model=JobResponse)
def extend_job(
    job_id: int,
    data: JobExtendRequest,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Gia hạn tin tuyển dụng sắp hết hạn hoặc đã hết hạn (FR-M2-05, Bảng 3.7.1)."""
    return job_service.extend_job(db, user, job_id, data)


@employer_router.delete("/{job_id}")
def delete_draft_job(
    job_id: int,
    user: User = Depends(employer_only),
    db: Session = Depends(get_db),
):
    """Xóa tin nháp hoặc tin bị từ chối."""
    return job_service.delete_draft_job(db, user, job_id)


# ---------- Admin: Kiểm duyệt tin tuyển dụng (FR-M2-06, FR-M2-07, PB-017) ----------

admin_router = APIRouter(prefix="/api/v1/admin/jobs", tags=["Admin Jobs"])
admin_only = require_roles("ADMIN")


@admin_router.get("", response_model=JobListResponse)
def admin_list_jobs(
    status_filter: JobStatus | None = Query(None, alias="status", description="Lọc theo trạng thái tin"),
    company_id: int | None = Query(None, description="Lọc theo ID công ty"),
    q: str | None = Query(None, max_length=100, description="Tìm theo tiêu đề tin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Admin xem danh sách toàn bộ tin tuyển dụng (có phân trang và bộ lọc)."""
    return job_service.admin_list_jobs(db, status_filter, company_id, q, page, page_size)


@admin_router.get("/{job_id}", response_model=JobResponse)
def admin_get_job(
    job_id: int,
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Admin xem chi tiết tin tuyển dụng."""
    return job_service.admin_get_job(db, job_id)


@admin_router.post("/{job_id}/approve", response_model=JobResponse)
def approve_job(
    job_id: int,
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Admin duyệt tin tuyển dụng (PENDING -> APPROVED) (FR-M2-06)."""
    return job_service.approve_job(db, admin, job_id)


@admin_router.post("/{job_id}/reject", response_model=JobResponse)
def reject_job(
    job_id: int,
    data: JobRejectRequest,
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Admin từ chối tin tuyển dụng kèm lý do (PENDING -> REJECTED) (FR-M2-06, BR-14)."""
    return job_service.reject_job(db, admin, job_id, data.reason)


@admin_router.post("/{job_id}/remove", response_model=JobResponse)
def remove_job(
    job_id: int,
    data: JobRemoveRequest,
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Admin gỡ tin tuyển dụng vi phạm kèm lý do (FR-M2-07)."""
    return job_service.remove_job(db, admin, job_id, data.reason)

