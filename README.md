# Vieco – Nền tảng kết nối việc làm

Vieco kết nối ứng viên và nhà tuyển dụng. Nhóm gồm 4 thành viên, phụ trách M0 (danh mục/cấu hình), M1 (tài khoản/hồ sơ), M2 (tuyển dụng/ứng tuyển), M3 (thông báo/thống kê). Phạm vi module không đồng nghĩa mọi chức năng đã hoàn thiện.

## Công nghệ và chức năng hiện có

- Frontend HTML/CSS/JavaScript thuần; kiểm thử bằng Node.js test runner và jsdom.
- Backend Python, FastAPI, Uvicorn; xác thực JWT và bcrypt.
- Database MySQL qua SQLAlchemy/PyMySQL; quản lý schema bằng Alembic.
- Backend có API xác thực, hồ sơ ứng viên/CV, danh mục, hồ sơ công ty và tin tuyển dụng cùng luồng kiểm duyệt. Kiểm thử backend dùng pytest và SQLite cô lập.

## Cấu trúc

```text
Vieco/
├── docs/          # Hướng dẫn, thiết kế, yêu cầu và kiểm thử
├── source_code/
│   ├── client/    # Trang HTML, CSS, JS và test frontend
│   └── server/    # FastAPI, model, migration và test backend
└── archive/       # File khung cũ và artefact, không dùng để chạy ứng dụng
```

Xem [cấu trúc chi tiết và danh sách di chuyển](docs/PROJECT_STRUCTURE.md).

## Cài đặt và chạy

Làm theo [SETUP](docs/SETUP.md) để tạo môi trường Python, cấu hình database và cài dependency. Khi database đã được chuẩn bị, chạy trong hai terminal từ gốc repository:

```powershell
cd source_code/server
python run.py
```

```powershell
cd source_code/client
python -m http.server 5500
```

Các lệnh Python trên giả định đã kích hoạt đúng môi trường ảo. Mở frontend tại http://localhost:5500 và Swagger UI tại http://127.0.0.1:8000/docs. Frontend không có bước build hoặc script npm start/dev.

## Tài liệu

- [Hướng dẫn Windows chi tiết](docs/HUONG_DAN_CHAY_DU_AN.md)
- [Kiểm thử và checklist](docs/TEST_CHECKLIST.md)
- [Biểu mẫu nhà tuyển dụng PB-015](docs/PB-015.md)
- [Quy ước đóng góp](docs/CONTRIBUTING.md)
- [Review tuần 1 – báo cáo lịch sử](docs/WEEK1_REVIEW.md)

Dự án dựa trên SRS Vieco phiên bản 1.0, ngày 01/11/2026. Không commit .env, khóa bí mật hoặc dữ liệu uploads.