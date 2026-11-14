# Vieco — Nền tảng kết nối việc làm

Vieco kết nối ứng viên và nhà tuyển dụng. Dự án dùng frontend HTML/CSS/JavaScript, backend FastAPI, MySQL qua SQLAlchemy và Alembic. Xác thực dùng JWT Bearer và bcrypt; CV được lưu cục bộ và kiểm tra quyền khi tải; email dùng SMTP.

Kiến trúc được đối chiếu với tài liệu thiết kế JobContact ngày 15/11/2026. Đã bổ sung đủ 24 đường dẫn API cốt lõi trong tài liệu. Công nghệ được giữ theo mã nguồn đang phát triển, vì vậy dự án **chưa trùng hoàn toàn tech stack React/Vite/Tailwind + Express/Prisma trong bản Word**. Xem [bảng đối chiếu](docs/ARCHITECTURE_REVIEW.md) để biết phạm vi và giới hạn kiểm chứng.

## Cấu trúc

```text
Vieco/
├── docs/                  # Thiết kế, đối chiếu và hướng dẫn
├── source_code/
│   ├── client/            # pages; src/features, src/services, src/assets
│   └── server/            # routes → controllers → services → models
└── archive/               # Artefact lịch sử, không dùng để chạy
```

Xem [cấu trúc chi tiết](docs/PROJECT_STRUCTURE.md), [cài đặt](docs/SETUP.md) và [hướng dẫn Windows](docs/HUONG_DAN_CHAY_DU_AN.md).

## Chạy dự án

Sau khi cài dependency, cấu hình `.env`, chạy migration và seed theo SETUP, mở hai terminal từ gốc repository:

```powershell
cd source_code/server
python run.py
```

```powershell
cd source_code/client
python -m http.server 5500
```

Frontend: http://localhost:5500. API/Swagger: http://127.0.0.1:8000/docs. Frontend không cần npm build. Thiết lập SMTP theo `.env.example` để gửi xác thực email, đặt lại mật khẩu và thông báo sự kiện. Các giá trị trong `.env` hiện có không bị thay đổi bởi đợt chỉnh sửa kiến trúc.

## Kiểm thử

Backend: chạy `python -m pytest tests -q` tại `source_code/server` bằng Python của môi trường ảo. Frontend: chạy `npm ci` rồi `npm test` tại `source_code/client`. Kiểm thử backend dùng SQLite cô lập, không chạy migration/seed lên MySQL thật.

Không commit `.env`, mật khẩu hay dữ liệu uploads. Các báo cáo tuần 1 trong docs là lịch sử, không phản ánh trạng thái hiện hành.
