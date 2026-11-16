"""Ảnh công ty do nhà tuyển dụng tự tải lên: logo, ảnh bìa và ảnh không gian làm việc.

Ảnh công ty là nội dung công khai nên được phục vụ qua GET /api/v1/media/company/<tệp>.
Tệp lưu tại <UPLOAD_DIR>/company/ với tên ngẫu nhiên; thư mục CV vẫn không công khai.
Chỉ nhận JPG, PNG, WEBP (không nhận SVG vì có thể chứa mã script) và kiểm tra chữ ký đầu tệp.
"""
import os
import re
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.catalog import SystemSetting
from src.models.company import Company, CompanyImage
from src.models.user import User
from src.services import company_service

MEDIA_SUBDIR = "company"
MEDIA_PREFIX = "/media/company/"
FILE_NAME_RE = re.compile(r"[0-9a-f]{32}\.(jpg|png|webp)")
CHUNK_SIZE = 64 * 1024
DEFAULT_LOGO_MAX_MB = 2
PHOTO_MAX_MB = 5          # ảnh bìa và ảnh không gian làm việc
MAX_GALLERY_IMAGES = 6
MEDIA_TYPES = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
EXTENSION_ALIASES = {"jpg": "jpg", "jpeg": "jpg", "png": "png", "webp": "webp"}


def _detect(head: bytes) -> str | None:
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def logo_max_mb(db: Session) -> int:
    raw = db.query(SystemSetting.setting_value).filter(SystemSetting.setting_key == "image_max_size_mb").scalar()
    try:
        value = int(raw) if raw is not None else DEFAULT_LOGO_MAX_MB
    except ValueError:
        return DEFAULT_LOGO_MAX_MB
    return value if value > 0 else DEFAULT_LOGO_MAX_MB


def limits(db: Session) -> dict:
    return dict(logo_max_mb=logo_max_mb(db), photo_max_mb=PHOTO_MAX_MB, max_images=MAX_GALLERY_IMAGES,
                allowed_extensions=["jpg", "jpeg", "png", "webp"])


def _folder() -> str:
    return os.path.join(settings.UPLOAD_DIR, MEDIA_SUBDIR)


def _remove(url: str | None) -> None:
    """Xóa tệp ảnh cũ; chỉ đụng tới tệp do hệ thống tạo trong thư mục ảnh công ty."""
    name = (url or "").removeprefix(MEDIA_PREFIX)
    if url and url.startswith(MEDIA_PREFIX) and FILE_NAME_RE.fullmatch(name):
        try:
            os.remove(os.path.join(_folder(), name))
        except FileNotFoundError:
            pass


def _store(file: UploadFile, max_mb: int) -> str:
    """Lưu tệp ảnh hợp lệ và trả về URL công khai tương đối (/media/company/<tệp>)."""
    claimed = EXTENSION_ALIASES.get((file.filename or "").rsplit(".", 1)[-1].lower())
    if claimed is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Chỉ chấp nhận ảnh JPG, PNG hoặc WEBP")
    os.makedirs(_folder(), exist_ok=True)
    temp_path = os.path.join(_folder(), f"{uuid.uuid4().hex}.part")
    size, head = 0, b""
    try:
        with open(temp_path, "wb") as out:
            while chunk := file.file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_mb * 1024 * 1024:
                    raise HTTPException(413, f"Ảnh tối đa {max_mb} MB")
                if len(head) < 16:
                    head += chunk[: 16 - len(head)]
                out.write(chunk)
        if size == 0:
            raise HTTPException(422, "Tệp ảnh rỗng")
        kind = _detect(head)
        if kind is None or kind != claimed:
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Nội dung tệp không phải ảnh JPG, PNG hoặc WEBP hợp lệ")
        name = f"{uuid.uuid4().hex}.{kind}"
        os.replace(temp_path, os.path.join(_folder(), name))
    except BaseException:
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass
        raise
    return MEDIA_PREFIX + name


def _owned_company(db: Session, user: User) -> Company:
    company, member = company_service.get_membership_or_404(db, user)
    if member.member_role != "OWNER":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ chủ sở hữu công ty mới được thay đổi hình ảnh")
    return company


def list_images(db: Session, company: Company) -> list[dict]:
    rows = (db.query(CompanyImage).filter(CompanyImage.company_id == company.id)
            .order_by(CompanyImage.created_at, CompanyImage.id).all())
    return [dict(id=row.id, url=row.file_url) for row in rows]


def get_media(db: Session, user: User) -> dict:
    company, member = company_service.get_membership_or_404(db, user)
    return dict(logo_url=company.logo_url, cover_url=company.cover_url, images=list_images(db, company),
                can_edit=member.member_role == "OWNER", limits=limits(db))


def _set_single(db: Session, user: User, column: str, file: UploadFile | None, max_mb: int) -> dict:
    company = _owned_company(db, user)
    new_url = _store(file, max_mb) if file is not None else None
    old_url = getattr(company, column)
    setattr(company, column, new_url)
    try:
        db.commit()
    except BaseException:
        db.rollback()
        _remove(new_url)
        raise
    _remove(old_url)  # xóa tệp cũ sau khi DB đã ghi nhận tệp mới
    return get_media(db, user)


def set_logo(db: Session, user: User, file: UploadFile) -> dict:
    return _set_single(db, user, "logo_url", file, logo_max_mb(db))


def delete_logo(db: Session, user: User) -> dict:
    return _set_single(db, user, "logo_url", None, 0)


def set_cover(db: Session, user: User, file: UploadFile) -> dict:
    return _set_single(db, user, "cover_url", file, PHOTO_MAX_MB)


def delete_cover(db: Session, user: User) -> dict:
    return _set_single(db, user, "cover_url", None, 0)


def add_image(db: Session, user: User, file: UploadFile) -> dict:
    company = _owned_company(db, user)
    if db.query(CompanyImage.id).filter(CompanyImage.company_id == company.id).count() >= MAX_GALLERY_IMAGES:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Tối đa {MAX_GALLERY_IMAGES} ảnh không gian làm việc, hãy xóa bớt ảnh cũ")
    url = _store(file, PHOTO_MAX_MB)
    db.add(CompanyImage(company_id=company.id, file_url=url))
    try:
        db.commit()
    except BaseException:
        db.rollback()
        _remove(url)
        raise
    return get_media(db, user)


def delete_image(db: Session, user: User, image_id: int) -> dict:
    company = _owned_company(db, user)
    row = db.query(CompanyImage).filter(CompanyImage.id == image_id, CompanyImage.company_id == company.id).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ảnh")
    url = row.file_url
    db.delete(row)
    db.commit()
    _remove(url)
    return get_media(db, user)


def file_for_serving(file_name: str) -> tuple[str, str]:
    """Chỉ phục vụ tệp có tên đúng mẫu do hệ thống sinh ra, chặn dò đường dẫn (../)."""
    if not FILE_NAME_RE.fullmatch(file_name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ảnh")
    path = os.path.join(_folder(), file_name)
    if not os.path.isfile(path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ảnh")
    return path, MEDIA_TYPES[file_name.rsplit(".", 1)[-1]]
