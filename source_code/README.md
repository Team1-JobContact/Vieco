# Mã nguồn Vieco

- `client/`: frontend HTML/CSS/JavaScript thuần. Trang HTML trong `pages/`; JS chia theo `assets/js/auth/`, `assets/js/employer/`, `assets/js/home/`. Chạy HTTP server từ client, kiểm thử bằng `npm test` sau khi cài dependency tại client.
- `server/`: backend FastAPI. Chạy `python run.py` từ server bằng Python của môi trường ảo. Nghiệp vụ trong `src/services/`, HTTP trong `src/routes/`, xác thực/phân quyền dùng `src/dependencies/auth.py`.

Xem [SETUP](../docs/SETUP.md), [cấu trúc dự án](../docs/PROJECT_STRUCTURE.md) và [hướng dẫn migration/seed](server/migrations/README.md).

Schema do Alembic quản lý. Đăng ký cần dữ liệu roles; seed chỉ tạo Admin khi có ADMIN_EMAIL và ADMIN_PASSWORD trong môi trường. Đặt SECRET_KEY riêng trong .env; không đưa thông tin bí mật vào Git.

Chạy test backend tại server bằng `python -m pytest tests -q`. Test dùng SQLite, không chứng minh migration tương thích MySQL thực tế. Migration/seed không được tự động thực hiện khi chạy test hoặc frontend.

Các file khung Express/Prisma đã được chuyển vào [archive](../archive/README.md); chúng không thuộc luồng chạy hiện tại.