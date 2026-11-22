from fastapi import Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middlewares.auth import require_roles
from src.models.user import User
from src.schemas.candidate import (
    CVListResponse, CVResponse, ProfileCreate, ProfileResponse, ProfileUpdate,
)
from src.schemas.cv_builder import CVAIRequest, CVAIResponse, CVBuilderData, CVBuilderResponse
from src.services import avatar_service, candidate_service, cv_ai_service, cv_service

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


# ---------- Trình tạo CV ----------

def _builder_data(data: str) -> dict:
    """Trường form `data` là JSON nội dung CV; lỗi trả 422 kèm thông báo tiếng Việt như các form khác."""
    try:
        return CVBuilderData.model_validate_json(data).model_dump()
    except ValidationError as error:
        first = error.errors(include_url=False)[0]
        message = "Dữ liệu CV không hợp lệ" if first["type"].startswith("json") else first["msg"].removeprefix("Value error, ")
        raise HTTPException(422, message)


def create_builder_cv(file: UploadFile = File(...), data: str = Form(...), user: User = Depends(candidate_only),
                      db: Session = Depends(get_db)):
    builder_data = _builder_data(data)
    profile = candidate_service.get_or_create_profile(db, user)
    return cv_service.upload_cv(db, profile, file, builder_data=builder_data)


def get_builder_cv(cv_id: int, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = candidate_service.get_profile_or_404(db, user)
    cv = cv_service.get_builder_cv_or_404(db, profile, cv_id)
    return CVBuilderResponse(cv=CVResponse.model_validate(cv), data=cv.builder_data)


def update_builder_cv(cv_id: int, file: UploadFile = File(...), data: str = Form(...),
                      user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    builder_data = _builder_data(data)
    profile = candidate_service.get_profile_or_404(db, user)
    return cv_service.upload_cv(db, profile, file, builder_data=builder_data, replace_id=cv_id)


def generate_cv_with_ai(data: CVAIRequest, user: User = Depends(candidate_only)):
    return CVAIResponse(data=cv_ai_service.generate(user, data.text, data.target))


def upload_avatar(file: UploadFile = File(...), user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return avatar_service.set_avatar(db, user, file)


def delete_avatar(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return avatar_service.set_avatar(db, user)
