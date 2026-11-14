# Cấu trúc dự án Vieco

Cấu trúc hiện tại áp dụng phân lớp của thiết kế JobContact trên nền tảng đang có: HTML/JavaScript và FastAPI/SQLAlchemy. Đây là sự tương ứng về trách nhiệm, không phải chuyển đổi sang React hoặc Express. Quyết định và bảng đối chiếu API nằm trong [ARCHITECTURE_REVIEW](ARCHITECTURE_REVIEW.md).

```text
source_code/
├── client/
│   ├── index.html
│   ├── pages/                    # login, register, employer, account
│   ├── src/
│   │   ├── assets/css/            # CSS hiện có
│   │   ├── features/
│   │   │   ├── auth/              # auth-ui, account-ui
│   │   │   ├── employer/          # biểu mẫu công ty/tin
│   │   │   └── jobs/              # danh sách, tìm kiếm, chi tiết
│   │   └── services/              # auth-api, account-api, employer-api, jobs-api
│   ├── tests/                    # Node test runner + jsdom
│   └── package.json
└── server/
    ├── run.py                    # Entry point Uvicorn
    ├── .env.example
    ├── requirements.txt
    ├── alembic.ini
    ├── migrations/               # Schema và lịch sử Alembic
    ├── uploads/                  # Dữ liệu cục bộ, không di chuyển
    ├── tests/
    └── src/
        ├── app.py                # Khởi tạo FastAPI và gắn router
        ├── config/               # Settings, database, SMTP transport
        ├── routes/               # URL, method, response/status
        ├── controllers/          # HTTP binding, validation, RBAC dependency
        ├── middlewares/          # Xác thực JWT, thu hồi token, phân quyền
        ├── dependencies/         # Import auth tương thích với mã cũ
        ├── services/             # Nghiệp vụ, transaction, truy vấn dữ liệu
        ├── models/               # Model SQLAlchemy
        ├── schemas/              # Request/response Pydantic
        ├── utils/                # JWT, bcrypt
        └── seeds/                # Dữ liệu ban đầu; chỉ chạy chủ động
```

Các thư mục trống cũ có thể còn trên máy; cây trên chỉ mô tả phần có mã đang chạy. Các thư mục components/layouts/routes dành riêng cho React chưa được sử dụng vì frontend hiện là các trang HTML tĩnh.

## Tương ứng với bản thiết kế

| Thiết kế | Hiện tại | Lý do |
| --- | --- | --- |
| client/public, src/assets | client/src/assets và HTML tại gốc/pages | HTTP server tĩnh, không có bước Vite build |
| client/src/features | client/src/features | UI gom theo nghiệp vụ |
| client/src/services | client/src/services | Tách HTTP client khỏi UI |
| React components/layouts/AppRoutes | HTML pages và các UI script | Chưa chuyển framework; chưa có SPA router |
| server/src/controllers | server/src/controllers | Controller nhận request và chuyển cho service |
| server/src/middlewares | server/src/middlewares | FastAPI dependency thực hiện auth/RBAC |
| server/src/services/models/config/utils/routes | Các thư mục cùng tên | Phân lớp theo trách nhiệm |
| server/src/app.js, server.js | server/src/app.py, run.py | Entry point tương ứng FastAPI |
| server/prisma | server/migrations + alembic.ini | SQLAlchemy/Alembic đang quản lý MySQL |
| Multer, Nodemailer | UploadFile + cv_service, smtplib + email_service | Công cụ tương ứng trong Python |

## Di chuyển trong đợt chỉnh kiến trúc

Bảng này dùng đường dẫn trước bước chỉnh kiến trúc, sau một giai đoạn gom JS trung gian. Thành viên cập nhật trực tiếp từ main xem bảng đường dẫn main → nhánh bàn giao tại [TEAM_CHANGE_REPORT](TEAM_CHANGE_REPORT.md#3-đường-dẫn-cần-dùng-khi-phát-triển-tiếp).

| Trước | Sau |
| --- | --- |
| client/assets/css/*.css | client/src/assets/css/*.css |
| client/assets/js/auth/auth-api.js | client/src/services/auth-api.js |
| client/assets/js/employer/employer-api.js | client/src/services/employer-api.js |
| client/assets/js/auth/auth-ui.js | client/src/features/auth/auth-ui.js |
| client/assets/js/employer/employer-ui.js | client/src/features/employer/employer-ui.js |
| client/assets/js/home/home-ui.js | client/src/features/jobs/home-ui.js |
| server/src/dependencies/auth.py | server/src/middlewares/auth.py; file cũ re-export để tương thích |
| Handler nằm trong server/src/routes/*.py | server/src/controllers/*_controller.py |
| docs/JobContact_System_Architecture_and_APIs.md thực chất là ZIP Word | docs/JobContact_System_Architecture_and_APIs.docx giữ nguyên byte; .md trở thành chỉ dẫn văn bản |

Tham chiếu HTML, kiểm thử và tài liệu vận hành đã đổi theo đường dẫn mới. URL trang cũ và API cũ vẫn tồn tại; API cốt lõi theo tài liệu được bổ sung tại `server/src/routes/core.py`. Không đổi các revision Alembic, dữ liệu uploads, `.env`, tên bảng hay vị trí client/server.
