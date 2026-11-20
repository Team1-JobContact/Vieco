# Cài đặt và chạy Vieco

Kết quả mới nhất: [review 17/11/2026](REVIEW_2026-11-17.md) và [lệnh chạy Windows](HUONG_DAN_CHAY_DU_AN.md). Backend hiện từ chối SECRET_KEY mặc định/placeholder hoặc dưới 32 ký tự; `.env.example` phải được điền khóa riêng trước khi chạy.

Để cả nhóm dùng cùng database, ảnh và CV, xem [hệ thống dùng chung](SHARED_SYSTEM.md).

Báo cáo kiểm tra mới: [18/11/2026](HOSTING_REVIEW_20261118.md). Hướng dẫn hosting: [Render từng bước](HOSTING_RENDER.md).

Bản bàn giao hiện tại và các việc cần làm khi cập nhật từ main xem [TEAM_CHANGE_REPORT](TEAM_CHANGE_REPORT.md).

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
| UPLOAD_DIR | Thư mục lưu tệp. Đường dẫn tương đối được tính từ source_code/server |
| ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME | Dữ liệu Admin cho seed; tài khoản chỉ được tạo khi có email và password |
| FRONTEND_URL | Địa chỉ frontend dùng trong liên kết email và danh sách CORS |
| CORS_ORIGINS | Mảng JSON các origin frontend bổ sung, mặc định []; FRONTEND_URL luôn được phép |

Khởi động MySQL và chuẩn bị database phát triển khớp DATABASE_URL. Xem [migration/seed](../source_code/server/migrations/README.md). Với database phát triển đã xác định đúng, các lệnh khởi tạo tại server là:

```powershell
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m src.seeds.run
```

Migration thay đổi schema. Seed ghi dữ liệu danh mục, vai trò và tùy chọn Admin. Tài khoản đã tồn tại được bỏ qua, vì vậy sửa ADMIN_PASSWORD trong .env không đặt lại mật khẩu trong database.

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

Khi frontend phát triển chạy trên localhost, 127.0.0.1 hoặc [::1] ở cổng 5500, API mặc định là http://127.0.0.1:8000/api/v1. Static Site https://vieco-frontend.onrender.com dùng API https://vieco.onrender.com/api/v1. Chế độ chạy chung trên cổng 8000 hoặc cổng HTTP(S) chuẩn dùng cùng origin cho website/API. Cấu hình dùng chung nằm tại `src/services/auth-api.js`; nếu tách frontend/backend trên tên miền khác, đặt `window.VIECO_API_BASE_URL` trước khi nạp script hoặc `localStorage.vieco_api_base_url` của frontend để ghi đè. Giữ tiền tố /api/v1. Khi chạy frontend ở origin khác, thêm origin tương ứng vào CORS_ORIGINS rồi khởi động lại backend.

## Triển khai frontend trên Render

Backend hiện tại là https://vieco.onrender.com; kiểm tra tiến trình tại https://vieco.onrender.com/api/v1/health hoặc Swagger tại https://vieco.onrender.com/docs. Trang gốc backend có thể trả 404 vì không phục vụ frontend.

Static Site `vieco-frontend` đã được xác minh tại https://vieco-frontend.onrender.com. Với hai dịch vụ hiện tại, đặt trên Environment của backend:

```ini
FRONTEND_URL=https://vieco-frontend.onrender.com
```

1. Tạo hoặc mở dịch vụ **Static Site** cho repository này. Đặt **Root Directory** là `source_code/client`, **Build Command** là `echo "Static frontend: no build required"`, **Publish Directory** là `.`. Frontend HTML/CSS/JS không cần npm build. Nếu đã có Static Site, đối chiếu các giá trị trước khi thay đổi.
2. Sao chép URL của **Static Site** trong Overview, mở trang chủ và `/pages/login.html`. URL này khác URL backend `https://vieco.onrender.com`.
3. Triển khai mã nguồn mới để frontend gọi `https://vieco.onrender.com/api/v1`. Nếu trình duyệt từng lưu API tùy chỉnh, mở Console tại website frontend và chạy `localStorage.removeItem("vieco_api_base_url")`, rồi tải lại trang.
4. Tại Render → backend `vieco` → Environment, đặt `FRONTEND_URL` bằng URL Static Site thật, chỉ gồm `https://tên-miền`, không thêm đường dẫn. Lưu và chờ backend triển khai lại. Biến này dùng cho CORS và các liên kết email. CORS chỉ cho phép origin đã cấu hình; khi dùng cấu hình phát triển mặc định, cả localhost:5500 và 127.0.0.1:5500 được chấp nhận.
5. Mở DevTools → Network tại frontend, thử đăng ký, đăng nhập, xem hồ sơ và danh sách việc làm. Request phải tới backend với tiền tố `/api/v1`; preflight OPTIONS phải thành công và response phải có `Access-Control-Allow-Origin` khớp URL frontend. Đăng ký phải trả 201, đăng nhập trả 200. Chỉ kiểm tra health chưa đủ xác nhận database hoạt động.

Không đặt URL backend vào `FRONTEND_URL`. Cấu hình Environment trên Render độc lập với `.env` cục bộ và `.env.example` trong repository.

Nếu health trả 200 nhưng `/api/v1/categories` hoặc `/api/v1/jobs` trả 500, mở Render → backend → Logs ngay sau khi gọi API và đọc traceback. Đối chiếu `DATABASE_URL` với database đã triển khai; nếu log báo thiếu bảng, kiểm tra migration; nếu báo thiếu vai trò, kiểm tra seed. Xem [hướng dẫn migration/seed](../source_code/server/migrations/README.md) và chỉ chạy trên database đích đã xác định. Lỗi 500 không đủ để kết luận nguyên nhân là CORS hoặc database.

Tham khảo cấu hình dịch vụ trong [hướng dẫn triển khai chính thức của Render](https://render.com/docs/your-first-deploy).

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

Kết quả kiểm tra ngày 18/11/2026: 103 test backend và 24 test frontend đạt. Bộ test dùng SQLite/jsdom và SMTP giả lập; ngoài ra đã kiểm tra migration/snapshot trên MySQL 8.0 thật, 49 kiểm tra HTTP và 38 lượt trang/kích thước trên Chrome thật. Chưa xác minh Aiven bằng CA của nhóm, SMTP thật, Docker/Linux hoặc HTTPS trên hosting. Chi tiết và giới hạn nằm trong [báo cáo trước hosting](HOSTING_REVIEW_20261118.md). Các con số 44/19, 52/21 trong báo cáo cũ thuộc các đợt kiểm tra trước.

Xem thêm [hướng dẫn Windows](HUONG_DAN_CHAY_DU_AN.md), [checklist](TEST_CHECKLIST.md) và [PB-015](PB-015.md). Không commit .env, token, mật khẩu hoặc dữ liệu uploads.

## Cập nhật kiến trúc ngày 15/11/2026

Xem [cấu trúc](PROJECT_STRUCTURE.md) và [bảng đối chiếu Word](ARCHITECTURE_REVIEW.md). Dự án giữ FastAPI/SQLAlchemy và frontend tĩnh; không cần cài Express/Prisma/React để chạy mã hiện tại. Không có migration mới trong đợt này.

Để bật email, thêm SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM, SMTP_STARTTLS, SMTP_SSL và FRONTEND_URL theo `source_code/server/.env.example`. Dùng STARTTLS với cổng 587 hoặc SSL với 465 theo máy chủ email. FRONTEND_URL phải trỏ tới HTTP server frontend thật, ví dụ http://localhost:5500. Mở lại backend sau khi sửa cấu hình. Không ghi đè `.env` đã có bằng file mẫu nếu chưa giữ lại giá trị kết nối/secret của mình.

Swagger tại http://127.0.0.1:8000/docs có cả API chuẩn theo thiết kế và API cũ để tương thích. GET /api/v1/health chỉ kiểm tra tiến trình API, không xác nhận kết nối MySQL.
