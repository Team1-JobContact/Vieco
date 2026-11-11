"""Quản lý CV (FR-M1-11): tải lên, xem danh sách, tải về, đặt mặc định, xóa.

Giới hạn lấy từ bảng system_settings (cv_max_size_mb, cv_max_count, cv_allowed_extensions),
mặc định theo SRS: PDF/DOC/DOCX, tối đa 5 MB mỗi tệp, tối đa 5 CV mỗi hồ sơ.
Tệp lưu tại <UPLOAD_DIR>/cvs/ với tên ngẫu nhiên và KHÔNG được public tĩnh (NFR-07, BR-16).
"""
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.catalog import SystemSetting
from src.models.profile import CV, CandidateProfile
from src.models.recruitment import Application

CV_SUBDIR = "cvs"
CHUNK_SIZE = 64 * 1024
DEFAULT_MAX_SIZE_MB = 5
DEFAULT_MAX_COUNT = 5
DEFAULT_EXTENSIONS = ("pdf", "doc", "docx")

# Chữ ký đầu tệp để chặn đổi đuôi tệp (vd .exe -> .pdf)
MAGIC_BYTES = {
    "pdf": (b"%PDF-",),
    "doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),  # OLE2 (Word 97-2003)
    "docx": (b"PK\x03\x04",),                      # ZIP (Office Open XML)
}
MEDIA_TYPES = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass
class CVLimits:
    max_size_mb: int
    max_count: int
    allowed_extensions: tuple[str, ...]

    @property
    def max_size_bytes(self) -> int:
        return self.max_size_mb * 1024 * 1024


def _int_setting(raw: str | None, default: int) -> int:
    try:
        value = int(raw) if raw is not None else default
    except ValueError:
        return default
    return value if value > 0 else default


def get_limits(db: Session) -> CVLimits:
    rows = dict(
        db.query(SystemSetting.setting_key, SystemSetting.setting_value)
        .filter(SystemSetting.setting_key.in_(("cv_max_size_mb", "cv_max_count", "cv_allowed_extensions")))
        .all()
    )
    exts = tuple(
        e for e in (x.strip().lower().lstrip(".") for x in rows.get("cv_allowed_extensions", "").split(","))
        if e in MAGIC_BYTES  # chỉ nhận định dạng hệ thống biết kiểm tra
    ) or DEFAULT_EXTENSIONS
    return CVLimits(
        max_size_mb=_int_setting(rows.get("cv_max_size_mb"), DEFAULT_MAX_SIZE_MB),
        max_count=_int_setting(rows.get("cv_max_count"), DEFAULT_MAX_COUNT),
        allowed_extensions=exts,
    )


def _active_cvs(db: Session, profile: CandidateProfile):
    return db.query(CV).filter(CV.candidate_profile_id == profile.id, CV.deleted_at.is_(None))


def list_cvs(db: Session, profile: CandidateProfile) -> list[CV]:
    return _active_cvs(db, profile).order_by(CV.is_default.desc(), CV.created_at.desc(), CV.id.desc()).all()


def get_cv_or_404(db: Session, profile: CandidateProfile, cv_id: int) -> CV:
    cv = _active_cvs(db, profile).filter(CV.id == cv_id).first()
    if cv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy CV")
    return cv


def _abs_path(cv: CV) -> str:
    return os.path.join(settings.UPLOAD_DIR, cv.file_url)


def _clean_filename(name: str | None) -> str:
    name = os.path.basename((name or "").replace("\\", "/")).strip()
    name = "".join(ch for ch in name if ch.isprintable())
    return name[-255:] if name else "cv"


def extension_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def upload_cv(db: Session, profile: CandidateProfile, file: UploadFile) -> CV:
    limits = get_limits(db)
    file_name = _clean_filename(file.filename)
    ext = extension_of(file_name)
    if ext not in limits.allowed_extensions:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            f"Chỉ chấp nhận tệp {', '.join(e.upper() for e in limits.allowed_extensions)}")

    count = _active_cvs(db, profile).count()
    if count >= limits.max_count:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Mỗi hồ sơ chỉ được tối đa {limits.max_count} CV, hãy xóa bớt CV cũ")

    folder = os.path.join(settings.UPLOAD_DIR, CV_SUBDIR)
    os.makedirs(folder, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(folder, stored_name)

    size = 0
    head = b""
    try:
        with open(path, "wb") as out:
            while chunk := file.file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > limits.max_size_bytes:  # dừng sớm, không đọc hết tệp quá lớn
                    raise HTTPException(413,
                                        f"Tệp CV tối đa {limits.max_size_mb} MB")
                if len(head) < 16:
                    head += chunk[: 16 - len(head)]
                out.write(chunk)
        if size == 0:
            raise HTTPException(422, "Tệp CV rỗng")
        if not head.startswith(MAGIC_BYTES[ext]):
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                "Nội dung tệp không đúng định dạng PDF/DOC/DOCX")

        cv = CV(candidate_profile_id=profile.id, file_name=file_name,
                file_url=f"{CV_SUBDIR}/{stored_name}", file_size=size,
                is_default=count == 0)  # CV đầu tiên tự thành mặc định
        db.add(cv)
        db.commit()
    except BaseException:
        db.rollback()
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        raise
    db.refresh(cv)
    return cv


def set_default(db: Session, profile: CandidateProfile, cv_id: int) -> CV:
    cv = get_cv_or_404(db, profile, cv_id)
    _active_cvs(db, profile).filter(CV.id != cv.id).update({CV.is_default: False}, synchronize_session=False)
    cv.is_default = True
    db.commit()
    db.refresh(cv)
    return cv


def delete_cv(db: Session, profile: CandidateProfile, cv_id: int) -> None:
    """CV đã gắn với đơn ứng tuyển thì xóa mềm (giữ tệp cho nhà tuyển dụng, BR-15); ngược lại xóa hẳn."""
    cv = get_cv_or_404(db, profile, cv_id)
    was_default = cv.is_default
    used = db.query(Application.id).filter(Application.cv_id == cv.id).first() is not None
    path = _abs_path(cv)

    if used:
        cv.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        cv.is_default = False
    else:
        db.delete(cv)
    db.flush()

    if was_default:  # chuyển mặc định sang CV mới nhất còn lại
        nxt = _active_cvs(db, profile).order_by(CV.created_at.desc(), CV.id.desc()).first()
        if nxt is not None:
            nxt.is_default = True
    db.commit()

    if not used:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def file_for_download(cv: CV) -> tuple[str, str]:
    path = _abs_path(cv)
    if not os.path.isfile(path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tệp CV không còn trên máy chủ")
    return path, MEDIA_TYPES.get(extension_of(cv.file_name), "application/octet-stream")
