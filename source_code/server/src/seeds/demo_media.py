"""Gắn logo, ảnh bìa và ảnh không gian làm việc cho 10 công ty demo (xem demo_companies.py).

Chạy từ thư mục server/ sau khi đã chạy demo_companies:  python -m src.seeds.demo_media

- Ảnh nằm trong src/seeds/demo_media/<công ty>/ (logo.png, cover.jpg, img1..3.jpg); nguồn và giấy phép xem CREDITS.md.
- Đi qua đúng nghiệp vụ tải ảnh của nhà tuyển dụng (company_media_service): kiểm tra định dạng, dung lượng,
  quyền chủ sở hữu và lưu tệp vào <UPLOAD_DIR>/company/ như khi tải trên giao diện.
- Idempotent: công ty đã có logo, ảnh bìa hoặc ảnh không gian làm việc thì bỏ qua, không ghi đè ảnh của nhà tuyển dụng.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from starlette.datastructures import UploadFile

from src.config.database import SessionLocal
from src.models import User
from src.models.company import CompanyImage
from src.services import company_media_service, company_service

MEDIA_DIR = Path(__file__).resolve().parent / "demo_media"
COMPANY_KEYS = ["fpt", "viettel", "vinamilk", "vietcombank", "momo", "tiki", "ghn", "vietnamairlines", "longchau", "coteccons"]


def _upload(path: Path) -> UploadFile:
    return UploadFile(file=path.open("rb"), filename=path.name)


def run() -> None:
    db = SessionLocal()
    try:
        done = skipped = 0
        for key in COMPANY_KEYS:
            folder = MEDIA_DIR / key
            user = db.query(User).filter(User.email == f"tuyendung.{key}@vieco.click").first()
            if user is None:
                raise SystemExit(f"Chưa có tài khoản tuyendung.{key}@vieco.click, hãy chạy python -m src.seeds.demo_companies")
            company, _ = company_service.get_membership_or_404(db, user)
            has_gallery = db.query(CompanyImage.id).filter(CompanyImage.company_id == company.id).first() is not None
            if company.logo_url or company.cover_url or has_gallery:
                print(f"Bỏ qua (đã có ảnh): {company.name}")
                skipped += 1
                continue
            for setter, path in ((company_media_service.set_logo, folder / "logo.png"),
                                 (company_media_service.set_cover, folder / "cover.jpg")):
                upload = _upload(path)
                try:
                    setter(db, user, upload)
                finally:
                    upload.file.close()
            for path in sorted(folder.glob("img*.jpg")):
                upload = _upload(path)
                try:
                    company_media_service.add_image(db, user, upload)
                finally:
                    upload.file.close()
            print(f"Đã gắn ảnh: {company.name}")
            done += 1
        print(f"Xong: gắn ảnh cho {done} công ty, bỏ qua {skipped} công ty đã có ảnh.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
