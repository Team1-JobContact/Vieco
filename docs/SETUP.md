# Cài đặt và chạy Vieco

## Yêu cầu

Git, Python và pip, MySQL, Node.js/npm để chạy test frontend. Phiên bản thư viện backend nằm trong `source_code/server/requirements.txt`; dependency frontend nằm trong package.json và package-lock.json tại client. Repository chưa chốt phiên bản Python/Node tối thiểu; cần dùng phiên bản tương thích các dependency đó.

Các lệnh sau dùng PowerShell, bắt đầu tại gốc repository. Không cần cài Node dependency để phục vụ HTML/CSS/JS thuần.

## Backend

Tạo môi trường ảo nếu chưa có và cài thư viện:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r source_code/server/requirements.txt
cd source_code/server
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Sửa .env cục bộ, giữ nguyên cấu hình đang có nếu file đã tồn tại:

| Biến | Mục đích |
| --- | --- |
| DATABASE_URL | URL SQLAlchemy dạng mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE; mã hóa ký tự đặc biệt trong thông tin đăng nhập |
| SECRET_KEY | Khóa riêng dùng ký JWT; thêm vào .env, không dùng khóa mặc định khi triển khai |
| APP_NAME, DEBUG | Tên ứng dụng và debug; DEBUG dùng True/False |
| ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES | Thuật toán JWT và thời hạn token theo cấu hình hiện có |
| UPLOAD_DIR | Thư mục CV; mặc định uploads/ tính từ thư mục chạy server |
| ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME | Dữ liệu Admin cho seed; tài khoản chỉ được tạo khi có email và password |

Khởi động MySQL và chuẩn bị database phát triển khớp DATABASE_URL. Xem [migration/seed](../source_code/server/migrations/README.md). Với database phát triển đã xác định đúng, các lệnh khởi tạo tại server là:

```powershell
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m src.seeds.run
```

Migration thay đổi schema; seed ghi dữ liệu danh mục/roles và tùy chọn Admin. Đây là hướng dẫn để người vận hành chủ động chạy, không phải thao tác được thực hiện trong phiên refactoring. Không chạy vào database chưa xác định hoặc dùng downgrade để kiểm tra.

Chạy backend từ server để giữ đúng cách nạp .env, Alembic và đường dẫn uploads:

```powershell
..\..\.venv\Scripts\python.exe run.py
```

API: http://127.0.0.1:8000/api/v1; Swagger: http://127.0.0.1:8000/docs. Endpoint /api/v1/health hiện trả thông báo cố định, không thực hiện truy vấn kiểm tra kết nối MySQL.

## Frontend

Mở terminal mới từ gốc repository:

```powershell
cd source_code/client
..\..\.venv\Scripts\python.exe -m http.server 5500
```

Mở http://localhost:5500, đăng nhập tại /pages/login.html hoặc mở /pages/employer.html. Dùng HTTP thay vì mở file HTML trực tiếp. Frontend không có script build/start/dev.

API mặc định là http://127.0.0.1:8000/api/v1, khai báo tại `assets/js/auth/auth-api.js`. Có thể dùng `window.VIECO_API_BASE_URL` trước khi nạp script, hoặc `localStorage.vieco_api_base_url` của frontend. Giữ tiền tố /api/v1. Không đổi CORS hoặc cấu hình bảo mật chỉ để tổ chức thư mục.

## Kiểm thử

Frontend, từ client:

```powershell
npm ci
npm test
```

Backend, từ server:

```powershell
$env:DEBUG='False'
..\..\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

DEBUG ở đây chỉ áp dụng tiến trình terminal, không sửa .env. Test backend dùng SQLite cô lập; test tích hợp cần Node trong PATH để gọi `client/tests/job-contract.cjs`. Nếu thiếu Node, test tích hợp có thể bị skip: phải đọc kết quả thay vì coi là đã xác minh.

Kết quả đã ghi nhận trong các bước refactoring: 44 test backend pass trước/sau đổi import auth; 19 test frontend pass trước/sau di chuyển JS; test tích hợp pass sau di chuyển JS. Chưa xác minh MySQL/migration thực tế và giao diện trực quan trên trình duyệt trong phiên này.

Xem thêm [hướng dẫn Windows](HUONG_DAN_CHAY_DU_AN.md), [checklist](TEST_CHECKLIST.md) và [PB-015](PB-015.md). Không commit .env, token, mật khẩu hoặc dữ liệu uploads.