# Tệp lưu trữ của dự án Vieco

Thư mục này giữ nguyên nội dung các file khung và artefact được chuyển khỏi mã nguồn đang hoạt động. Đây không phải thành phần cần chạy hoặc cài đặt dependency.

| Đường dẫn cũ từ gốc repository | Đường dẫn mới từ gốc repository | Lý do |
| --- | --- | --- |
| `source_code/server/server.js` | `archive/source_code/server/server.js` | File khung khởi chạy máy chủ JavaScript, chỉ có comment. |
| `source_code/server/src/app.js` | `archive/source_code/server/src/app.js` | File khung Express, chỉ có comment. |
| `source_code/server/prisma/.gitkeep` | `archive/source_code/server/prisma/.gitkeep` | Placeholder Prisma; backend hiện dùng SQLAlchemy và Alembic. |
| `source_code/server/src/controllers/.gitkeep` | `archive/source_code/server/src/controllers/.gitkeep` | Placeholder controllers cũ; backend hiện có controller thực tế trong source_code/server/src/controllers. |
| `source_code/New Text Document.txt` | `archive/source_code/New Text Document.txt` | File văn bản rỗng. |
| `package-lock.json` | `archive/package-lock.json` | Lockfile gốc rỗng, không có package.json tương ứng. |

Backend đang hoạt động nằm tại `source_code/server`, khởi chạy bằng `python run.py` từ thư mục đó. Frontend và lockfile dùng cho kiểm thử vẫn nằm tại `source_code/client`.

Không chạy npm hoặc Prisma trong archive. Không lưu .env, thông tin bí mật hoặc dữ liệu uploads tại đây. Để hoàn tác bước di chuyển, đưa từng file trong bảng về đường dẫn cũ nếu vị trí đó chưa có file khác; không ghi đè thay đổi mới.