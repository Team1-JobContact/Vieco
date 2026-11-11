from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.candidate import (
    CVListResponse, CVResponse, ProfileCreate, ProfileResponse, ProfileUpdate,
)
from src.services import candidate_service, cv_service

router = APIRouter(prefix="/api/v1/candidates/me", tags=["Candidate"])
candidate_only = require_roles("CANDIDATE")


# ---------- Hồ sơ ứng viên ----------

@router.get("/profile", response_model=ProfileResponse)
def get_profile(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    return candidate_service.to_profile_response(profile, user)


@router.post("/profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(data: ProfileCreate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return candidate_service.create_profile(db, user, data)


@router.patch("/profile", response_model=ProfileResponse)
def update_profile(data: ProfileUpdate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return candidate_service.update_profile(db, user, data)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    candidate_service.delete_profile(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- CV ----------

@router.get("/cvs", response_model=CVListResponse)
def list_cvs(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    limits = cv_service.get_limits(db)
    profile = candidate_service.find_profile(db, user)
    items = cv_service.list_cvs(db, profile) if profile else []
    return CVListResponse(items=items, total=len(items), max_count=limits.max_count,
                          max_size_mb=limits.max_size_mb,
                          allowed_extensions=list(limits.allowed_extensions))


@router.post("/cvs", response_model=CVResponse, status_code=status.HTTP_201_CREATED)
def upload_cv(file: UploadFile = File(...), user: User = Depends(candidate_only),
              db: Session = Depends(get_db)):
    profile = candidate_service.get_or_create_profile(db, user)
    return cv_service.upload_cv(db, profile, file)


@router.get("/cvs/{cv_id}/download")
def download_cv(cv_id: int, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    cv = cv_service.get_cv_or_404(db, profile, cv_id)
    path, media_type = cv_service.file_for_download(cv)
    return FileResponse(path, media_type=media_type, filename=cv.file_name)


@router.patch("/cvs/{cv_id}/default", response_model=CVResponse)
def set_default_cv(cv_id: int, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    return cv_service.set_default(db, profile, cv_id)


@router.delete("/cvs/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv(cv_id: int, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    cv_service.delete_cv(db, profile, cv_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
