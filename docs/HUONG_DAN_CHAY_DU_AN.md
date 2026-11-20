# Chạy Vieco trên Windows — kiểm tra ngày 17/11/2026

Dự án thực tế: frontend HTML/CSS/JavaScript tại `source_code/client`; backend FastAPI tại `source_code/server`; MySQL qua SQLAlchemy/Alembic. Không cài Express, Prisma, React hay Live Server để chạy mã hiện tại. `archive/` chỉ giữ mã cũ.

## 1. Phần mềm

- Python và pip. Môi trường hiện có đã test bằng Python **3.15.2**.
- MySQL Server. Đã kiểm chứng bằng **MySQL 8.0.45**; schema cần MySQL hỗ trợ CHECK constraint.
- Node.js/npm nếu chạy test frontend: đã test bằng Node **24.13.0**, npm **11.6.2**. Chạy giao diện không cần Node.

Tại thời điểm review, dịch vụ **MySQL80 đang dừng**. Mở PowerShell **Run as administrator** và chạy:

```powershell
Start-Service -Name MySQL80
Get-Service -Name MySQL80
```

Sau đó dùng terminal thông thường cho các bước sau. Không cần đổi execution policy hoặc activate môi trường ảo.

## 2. Cài dependencies và tạo .env nếu chưa có

```powershell
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco'
if (-not (Test-Path '.\.venv\Scripts\python.exe')) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r .\source_code\server\requirements.txt
.\.venv\Scripts\python.exe -m pip check
if (-not (Test-Path '.\source_code\server\.env')) { Copy-Item '.\source_code\server\.env.example' '.\source_code\server\.env' }
notepad .\source_code\server\.env
```

`.env` đã tồn tại trên máy này: giữ các giá trị đang dùng nếu đúng. Những giá trị phải kiểm tra:

```dotenv
DATABASE_URL=mysql+pymysql://root:MAT_KHAU_MYSQL@127.0.0.1:3306/job_contact_db
SECRET_KEY=KHOA_NGAU_NHIEN_RIENG_CUA_BAN
DEBUG=false
UPLOAD_DIR=uploads/
FRONTEND_URL=http://localhost:5500
CORS_ORIGINS=["http://localhost:5500","http://127.0.0.1:5500"]
ADMIN_EMAIL=admin@jobcontact.vn
ADMIN_PASSWORD=MAT_KHAU_ADMIN_BAN_TU_DAT
ADMIN_FULL_NAME=Quản trị viên
```

**Thay các giá trị viết hoa dạng MAT_KHAU/KHOA bằng giá trị thật.** DATABASE_URL phải khớp tài khoản MySQL của bạn. Mật khẩu MySQL có `@`, `:`, `%`, `#`... cần URL-encode phần mật khẩu. Không thay cả URL bằng một chuỗi đã encode.

SECRET_KEY phải là khóa riêng ít nhất 32 ký tự; backend từ chối khóa mặc định hoặc placeholder. Nếu chưa có khóa, tạo bằng:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Dán kết quả vào SECRET_KEY, giữ ổn định giữa các lần chạy. ADMIN_PASSWORD dùng ít nhất 8 ký tự gồm chữ và số, tối đa 72 byte. Seed chỉ tạo admin khi có email/password; **không đặt lại mật khẩu tài khoản đã tồn tại**.

SMTP là tùy chọn. Giữ SMTP_HOST trống để chạy chức năng tuyển dụng cục bộ; khi đó đăng ký/đăng nhập vẫn dùng được, nhưng không gửi xác thực và API quên mật khẩu trả 503. Để bật email, điền các biến SMTP theo `.env.example` bằng cấu hình nhà cung cấp, rồi khởi động lại backend. Review này không xác minh SMTP thật.

## 3. Tạo database, migration và seed

Lệnh sau dùng đúng vị trí MySQL 8.0 đã tìm thấy trên máy. Nhập mật khẩu MySQL khi được hỏi:

```powershell
& 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe' -u root -p -e "CREATE DATABASE IF NOT EXISTS job_contact_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco\source_code\server'
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m alembic current
..\..\.venv\Scripts\python.exe -m src.seeds.run
```

Nếu DATABASE_URL dùng tên database khác, thay `job_contact_db` trong câu CREATE DATABASE cho khớp. Migration hiện tại là **0003**, gồm **29 bảng ứng dụng + alembic_version**. Không dùng `alembic downgrade base` để xử lý lỗi chạy.

Seed tạo roles, ngành nghề, tỉnh/thành, kỹ năng, cấu hình, trang nội dung và admin tùy chọn. **Không seed công ty/tin tuyển dụng hay tài khoản ứng viên/nhà tuyển dụng mẫu.** Trang chủ có thể rỗng khi chưa có tin được duyệt.

## 4. Chạy backend — terminal thứ nhất

```powershell
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco\source_code\server'
..\..\.venv\Scripts\python.exe run.py
```

Giữ terminal mở. API: http://127.0.0.1:8000/api/v1; Swagger: http://127.0.0.1:8000/docs.

## 5. Chạy frontend — terminal thứ hai

```powershell
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco\source_code\client'
..\..\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Mở **http://localhost:5500**. Không mở HTML bằng file://. Frontend không cần npm build. Hai terminal dùng trực tiếp Python của `.venv`, không phụ thuộc interpreter mặc định trong PATH.

API mặc định trong `src/services/auth-api.js` là `http://127.0.0.1:8000/api/v1`. Nếu browser từng lưu API khác, mở Console trên frontend và chạy `localStorage.removeItem('vieco_api_base_url'); location.reload();`. Khi đổi cổng frontend, cập nhật FRONTEND_URL/CORS_ORIGINS tương ứng và khởi động lại backend.

## 6. Kiểm tra hoạt động — terminal thứ ba

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/health'
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/categories'
```

Health chỉ kiểm tra tiến trình; `/categories` phải trả về danh mục sau seed để xác minh API đọc được database.

Luồng kiểm tra đầy đủ:

1. Đăng nhập admin bằng ADMIN_EMAIL/ADMIN_PASSWORD đã seed ở `/pages/login.html`; mở `/pages/admin.html`.
2. Đăng ký một tài khoản **Nhà tuyển dụng**; tạo công ty ở `/pages/employer.html`.
3. Admin duyệt công ty; nhà tuyển dụng tạo tin đủ thông tin, gửi duyệt; admin duyệt tin.
4. Tin xuất hiện ở trang chủ và `/pages/jobs.html`; tìm kiếm, mở chi tiết.
5. Đăng ký một tài khoản **Ứng viên**; cập nhật hồ sơ, tải CV PDF/DOC/DOCX, ứng tuyển.
6. Nhà tuyển dụng xem đơn, tải CV, chuyển trạng thái; ứng viên xem lịch sử và thông báo.
7. Kiểm tra đóng tin, gia hạn, mở lại. Tin quá hạn hiển thị EXPIRED theo ngày Việt Nam; gia hạn tin hết hạn phải duyệt lại. Tin bị admin gỡ không thể tự mở lại.

Không có mật khẩu mẫu dùng chung. Tài khoản và dữ liệu trong kiểm thử của reviewer chỉ nằm trong database tạm, đã được dọn sau kiểm tra.

## 7. Chạy test khi cần

Backend **phải chạy từ server** để import package `src` đúng:

```powershell
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco\source_code\server'
..\..\.venv\Scripts\python.exe -m pytest tests -q
```

Frontend:

```powershell
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco\source_code\client'
npm.cmd ci
npm.cmd test
```

Kết quả ngày 17/11/2026: **105 backend**, **29 frontend** đạt. Bộ test backend thường dùng SQLite cô lập; review bổ sung kiểm tra migration, schema, seed, nghiệp vụ trên MySQL tạm và 22 kiểm tra Edge headless. Một cảnh báo deprecation từ Starlette TestClient không làm test thất bại.

## 8. Chạy lại dự án sau khi đã thoát tất cả

Sau khi đã cài đặt, cấu hình `.env`, migration và seed thành công, mỗi lần mở lại chỉ cần thực hiện các bước dưới đây. Cài dependencies, tạo database và seed thuộc bước thiết lập ban đầu; chỉ thực hiện lại khi có thay đổi yêu cầu tương ứng.

### Bước 1 — Kiểm tra MySQL

Mở PowerShell và chạy:

```powershell
Get-Service MySQL80
```

Nếu trạng thái là **Running**, chuyển sang bước 2. Nếu là **Stopped**, mở PowerShell bằng **Run as administrator** rồi chạy:

```powershell
Start-Service -Name MySQL80
Get-Service MySQL80
```

### Bước 2 — Chạy backend

Mở dự án trong VS Code, chọn **Terminal → New Terminal** và chạy:

```powershell
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco\source_code\server'
..\..\.venv\Scripts\python.exe run.py
```

Nhấn Enter sau khi nhập lệnh. Đợi thông báo **Application startup complete.** và giữ terminal này mở.

### Bước 3 — Chạy frontend

Nhấn nút **+** ở khu vực Terminal để mở terminal thứ hai, rồi chạy:

```powershell
Set-Location 'C:\Users\nandz\OneDrive\Documents\ThucTap_Nhom1\Dự án\Vieco 2\Vieco\source_code\client'
..\..\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Giữ terminal thứ hai mở và truy cập **http://localhost:5500**. Swagger của backend ở **http://127.0.0.1:8000/docs**. Thử đăng nhập và tải danh sách việc làm để kiểm tra dự án hoạt động.

### Dừng dự án

Nhấn **Ctrl + C** trong từng terminal backend và frontend. Giữ MySQL chạy nếu các ứng dụng khác còn sử dụng dịch vụ này.

## Lỗi thường gặp

| Hiện tượng | Xử lý |
| --- | --- |
| MySQL 2003/10061 | Dịch vụ MySQL chưa chạy, sai host/cổng; kiểm tra MySQL80 trước. |
| Access denied/Unknown database | Sửa DATABASE_URL, tài khoản/quyền hoặc tạo đúng database. |
| SECRET_KEY bị từ chối | Thay placeholder bằng khóa riêng sinh ở bước 2. |
| Thiếu bảng/cột | Chạy `python -m alembic upgrade head` bằng `.venv` tại server. |
| ModuleNotFoundError: src | Chạy backend/test từ `source_code/server`. |
| Lỗi CORS | Mở frontend ở localhost:5500; đối chiếu origin trong CORS_ORIGINS. |
| Quên mật khẩu trả 503 | SMTP_HOST chưa cấu hình; không phải lỗi database. |
| Đổi ADMIN_PASSWORD nhưng login vẫn sai | Seed bỏ qua tài khoản đã tồn tại; không reset password. |

Xem [báo cáo review](REVIEW_2026-11-17.md) để biết phạm vi sửa và phần chưa hoàn thiện.
