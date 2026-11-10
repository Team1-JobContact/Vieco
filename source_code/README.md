# Vieco

Cấu trúc dự án Vieco gồm `client/` (Frontend) và `server/` (Backend).
<!-- 
Cần lưu ý: Phần phân quyền - PB10(B)

Chạy migration và seed. Trước khi dùng thật, bạn cần chạy alembic upgrade head và python -m src.seeds.run. Nếu chưa seed bảng roles, đăng ký sẽ báo lỗi.
Đã sửa seeds/run.py. Phần tạo admin giờ dùng hash_password, vì passlib không chạy được với bcrypt 5.
Đã sửa requirements.txt. Mình bỏ passlib và cors, thêm pydantic[email], pytest và httpx, và nới các phiên bản để chạy được trên Python 3.14. Bạn nên báo team biết.
Chưa chạy migration 0002 trên MySQL thật. Nó mới chỉ được viết dựa trên migration 0001.
Đổi SECRET_KEY trong .env trước khi triển khai.

Chạy test bằng lệnh: cd source_code\server; python -m pytest tests. -->