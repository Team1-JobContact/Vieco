# Vieco — Nền tảng kết nối việc làm

Frontend HTML/CSS/JavaScript, backend FastAPI, SQLAlchemy/Alembic và MySQL. Xác thực JWT, mật khẩu bcrypt, email SMTP, CV/ảnh lưu tại backend. Xem [đối chiếu thiết kế](docs/ARCHITECTURE_REVIEW.md).

## Chạy trên Windows

Cần Python có pip và MySQL đang chạy; Node.js/npm để chạy test giao diện. Tại thư mục gốc, mở PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r source_code/server/requirements.txt
cd source_code/server
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Mở `source_code/server/.env`, đặt DATABASE_URL và SECRET_KEY riêng tối thiểu 32 ký tự. Không ghi đè cấu hình đang có. URL mẫu, phải thay bằng thông tin thật:

```dotenv
DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/job_contact_db
```

Mã hóa ký tự đặc biệt trong username/password của URL. Trong MySQL Workbench, tạo database local nếu chưa có:

```sql
CREATE DATABASE IF NOT EXISTS job_contact_db
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Sau khi xác nhận đúng database test, chạy tại server:

```powershell
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m src.seeds.run
..\..\.venv\Scripts\python.exe run.py
```

Admin chỉ được seed khi đặt ADMIN_EMAIL và ADMIN_PASSWORD trong .env; seed không đổi mật khẩu tài khoản đã tồn tại. Không có mật khẩu Admin mặc định.

Mở terminal thứ hai tại thư mục gốc:

```powershell
cd source_code/client
..\..\.venv\Scripts\python.exe -m http.server 5500
```

Website: http://localhost:5500 — Swagger: http://127.0.0.1:8000/docs.
Giữ cả hai terminal mở. Không cần npm build hoặc Live Server. API base URL mặc định: http://127.0.0.1:8000/api/v1.
Endpoint /api/v1/health chỉ kiểm tra tiến trình; /api/v1/ready trả 200 khi kết nối DB thành công, 503 khi lỗi.
Cấu hình SMTP và hướng dẫn chi tiết: [SETUP](docs/SETUP.md).

## Hệ thống dùng chung

Nhóm đã có một backend phục vụ website/API và file chung, kết nối MySQL Aiven bằng TLS. Xem [SHARED_SYSTEM](docs/SHARED_SYSTEM.md) và [HOSTING_RENDER](docs/HOSTING_RENDER.md). run_shared.py đọc .env.shared; run.py dùng .env. Dùng shared thì mở URL server thay vì frontend local cổng 5500.

## Database nhóm

localhost là máy chạy backend. Chép .env có localhost từ trưởng nhóm không kết nối vào database trưởng nhóm. Git không đồng bộ dữ liệu MySQL.

Muốn dùng chung: nhận host/port/database/tài khoản được cấp quyền, cấu hình DATABASE_URL rồi khởi động lại backend. Máy chủ phải cho phép máy thành viên kết nối qua mạng riêng/VPN hoặc danh sách IP; cấu hình TLS theo máy chủ. Một người phụ trách áp dụng migration; không tự seed/reset database chung.

Workbench là công cụ quản lý, không cần mở để web chạy. CV và ảnh ở uploads của từng backend: dùng chung MySQL chưa đồng nghĩa dùng chung file. Demo nhóm nên dùng một backend hoặc thống nhất nơi lưu file.

## Chẩn đoán lỗi

| Lỗi | Kiểm tra |
| --- | --- |
| Không kết nối API | Backend cổng 8000 và API base URL |
| Sai email/mật khẩu | Đúng DB và tài khoản chưa; seed không đổi mật khẩu cũ |
| MySQL 1045 | Username/password và quyền kết nối từ máy backend |
| MySQL 2003 | MySQL đang chạy, host/port, mạng và firewall |
| Thiếu database/bảng | Tạo database local; người phụ trách chạy migration |
| Đăng nhập bị giới hạn | Tạm khóa 15 phút sau 5 lần sai |
| Swagger mở nhưng thao tác lỗi | Kiểm tra API đọc/ghi DB và terminal, không chỉ health |

Frontend có thể ghi đè URL qua window.VIECO_API_BASE_URL hoặc khóa vieco_api_base_url trong localStorage của origin đang mở; giữ tiền tố /api/v1.

## Kiểm thử và bàn giao

Backend, tại source_code/server:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

Frontend, tại source_code/client:

```powershell
npm ci
npm test
```

Test dùng SQLite cô lập và jsdom, không thay thế nghiệm thu MySQL/SMTP/trình duyệt thật.

- [Hướng dẫn demo](docs/HUONG_DAN_DEMO.md)
- [Checklist nghiệm thu](docs/TEST_CHECKLIST.md)
- [Báo cáo T05C354 và tổng kết phạm vi](docs/T05C354_HANDOFF.md)
- [Cấu trúc dự án](docs/PROJECT_STRUCTURE.md)

Không commit .env, mật khẩu, token hoặc uploads. Báo cáo cũ có ngày riêng là tài liệu lịch sử.
