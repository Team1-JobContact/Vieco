from fastapi import Depends, File, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.candidate import (
    CVListResponse, CVResponse, ProfileCreate, ProfileResponse, ProfileUpdate,
)
from src.services import candidate_service, cv_service

candidate_only = require_roles("CANDIDATE")


# ---------- Hồ sơ ứng viên ----------

def get_profile(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    return candidate_service.to_profile_response(profile, user)


def create_profile(data: ProfileCreate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return candidate_service.create_profile(db, user, data)


def update_profile(data: ProfileUpdate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return candidate_service.update_profile(db, user, data)


def delete_profile(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    candidate_service.delete_profile(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- CV ----------

def list_cvs(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    limits = cv_service.get_limits(db)
    profile = candidate_service.find_profile(db, user)
    items = cv_service.list_cvs(db, profile) if profile else []
    return CVListResponse(items=items, total=len(items), max_count=limits.max_count,
                          max_size_mb=limits.max_size_mb,
                          allowed_extensions=list(limits.allowed_extensions))


def upload_cv(file: UploadFile = File(...), user: User = Depends(candidate_only),
              db: Session = Depends(get_db)):
    profile = candidate_service.get_or_create_profile(db, user)
    return cv_service.upload_cv(db, profile, file)


def download_cv(cv_id: int, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    cv = cv_service.get_cv_or_404(db, profile, cv_id)
    path, media_type = cv_service.file_for_download(cv)
    return FileResponse(path, media_type=media_type, filename=cv.file_name)


def set_default_cv(cv_id: int, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    return cv_service.set_default(db, profile, cv_id)


def delete_cv(cv_id: int, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    cv_service.delete_cv(db, profile, cv_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
