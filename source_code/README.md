# Mã nguồn Vieco

- `client/`: HTML/CSS/JavaScript; trang trong `pages/`, UI theo chức năng trong `src/features/`, HTTP client trong `src/services/`, CSS trong `src/assets/`. Chạy HTTP server từ client; kiểm thử bằng `npm test`.
- `server/`: FastAPI; `routes/` khai báo URL và response, `controllers/` nhận dữ liệu HTTP và dependency, `services/` xử lý nghiệp vụ, `models/` ánh xạ SQLAlchemy. `middlewares/auth.py` kiểm tra JWT và RBAC. `dependencies/auth.py` giữ import tương thích.

Xem [SETUP](../docs/SETUP.md), [cấu trúc](../docs/PROJECT_STRUCTURE.md), [đối chiếu thiết kế](../docs/ARCHITECTURE_REVIEW.md) và [migration/seed](server/migrations/README.md).

MySQL schema vẫn do Alembic quản lý. Không dùng thư mục `prisma/` rỗng làm bằng chứng dự án đã tích hợp Prisma. Bộ khung Express cũ trong archive không thuộc runtime.

Chạy backend tại server bằng `python run.py`; chạy test bằng `python -m pytest tests -q`. Đặt `SECRET_KEY` riêng trong `.env`. Seed Admin chỉ chạy khi có `ADMIN_EMAIL` và `ADMIN_PASSWORD`. File `.env.example` liệt kê biến cấu hình, bao gồm SMTP tùy chọn; không chứa thông tin đăng nhập thật.
