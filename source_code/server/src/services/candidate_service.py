"""Hồ sơ ứng viên (FR-M1-09, FR-M1-12): mỗi tài khoản ứng viên có tối đa một hồ sơ."""
import os

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.catalog import Province
from src.models.profile import CV, CandidateProfile
from src.models.recruitment import Application
from src.models.user import User
from src.schemas.candidate import ProfileCreate, ProfileResponse, ProfileUpdate

USER_FIELDS = ("full_name", "phone")


def to_profile_response(profile: CandidateProfile, user: User) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id, user_id=user.id, email=user.email, full_name=user.full_name,
        phone=user.phone, avatar_url=user.avatar_url,
        date_of_birth=profile.date_of_birth, gender=profile.gender, address=profile.address,
        province_id=profile.province_id, headline=profile.headline, summary=profile.summary,
        visibility=profile.visibility, created_at=profile.created_at, updated_at=profile.updated_at,
    )


def find_profile(db: Session, user: User) -> CandidateProfile | None:
    return db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()


def get_profile_or_404(db: Session, user: User) -> CandidateProfile:
    profile = find_profile(db, user)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bạn chưa tạo hồ sơ ứng viên")
    return profile


def get_or_create_profile(db: Session, user: User) -> CandidateProfile:
    """Dùng khi tải CV: tự tạo hồ sơ trống nếu ứng viên chưa có."""
    profile = find_profile(db, user)
    if profile is not None:
        return profile
    profile = CandidateProfile(user_id=user.id)
    db.add(profile)
    try:
        db.commit()
    except IntegrityError:  # request song song đã tạo trước
        db.rollback()
        return get_profile_or_404(db, user)
    db.refresh(profile)
    return profile


def _check_province(db: Session, province_id: int | None) -> None:
    if province_id is None:
        return
    ok = db.query(Province.id).filter(Province.id == province_id, Province.is_active.is_(True)).first()
    if ok is None:
        raise HTTPException(422, "Tỉnh/thành không tồn tại")


def _apply(profile: CandidateProfile, user: User, changes: dict) -> None:
    for key, value in changes.items():
        setattr(user if key in USER_FIELDS else profile, key, value)


def create_profile(db: Session, user: User, data: ProfileCreate) -> ProfileResponse:
    if find_profile(db, user) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ ứng viên đã tồn tại")
    changes = data.model_dump(exclude_unset=True)
    if changes.get("full_name") is None:
        changes.pop("full_name", None)  # giữ họ tên đã khai khi đăng ký
    if changes.get("visibility") is None:
        changes.pop("visibility", None)
    _check_province(db, changes.get("province_id"))

    profile = CandidateProfile(user_id=user.id)
    _apply(profile, user, changes)
    db.add(profile)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ ứng viên đã tồn tại")
    db.refresh(profile)
    db.refresh(user)
    return to_profile_response(profile, user)


def update_profile(db: Session, user: User, data: ProfileUpdate) -> ProfileResponse:
    profile = get_profile_or_404(db, user)
    changes = data.model_dump(exclude_unset=True)
    if "province_id" in changes:
        _check_province(db, changes["province_id"])
    _apply(profile, user, changes)
    db.commit()
    db.refresh(profile)
    db.refresh(user)
    return to_profile_response(profile, user)


def delete_profile(db: Session, user: User) -> None:
    """Xóa hồ sơ cùng học vấn/kinh nghiệm/kỹ năng (CASCADE) và toàn bộ CV.

    Không cho xóa khi hồ sơ đã có đơn ứng tuyển (BR-15: đơn phải tham chiếu hồ sơ và CV).
    """
    profile = get_profile_or_404(db, user)
    if db.query(Application.id).filter(Application.candidate_profile_id == profile.id).first():
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Hồ sơ đã có đơn ứng tuyển nên không thể xóa; hãy chuyển sang chế độ riêng tư")
    cvs = db.query(CV).filter(CV.candidate_profile_id == profile.id).all()
    paths = [os.path.join(settings.UPLOAD_DIR, cv.file_url) for cv in cvs]
    for cv in cvs:
        db.delete(cv)
    db.delete(profile)
    db.commit()
    for path in paths:  # xóa tệp sau khi commit để không mất tệp nếu DB lỗi
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
