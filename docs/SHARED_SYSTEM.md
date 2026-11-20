# Hệ thống dùng chung cho nhóm

Mọi thành viên mở **cùng một địa chỉ website**. Website và API chạy trên một backend, backend kết nối MySQL Aiven bằng TLS và giữ thư mục uploads chung. Máy thành viên không cần MySQL hoặc mật khẩu Aiven.

Xem [kết quả kiểm tra 18/11](HOSTING_REVIEW_20261118.md) và [hướng dẫn đưa lên Render](HOSTING_RENDER.md). Chế độ shared yêu cầu DEBUG=false, SECRET_KEY riêng ít nhất 32 ký tự và URL database được đặt rõ; Aiven cần bật TLS. CORS_ORIGINS chỉ cần bổ sung nếu frontend chạy trên một origin riêng.

## Chuẩn bị trên máy chạy backend

File riêng `source_code/server/.env.shared` chứa kết nối Aiven, SECRET_KEY và `DATABASE_SSL=true`; file này được Git bỏ qua. Cấu hình phát triển `.env` vẫn dùng riêng khi chạy `python run.py`.

Tại Aiven Console → dịch vụ MySQL → Overview → Connection information, tải **CA Certificate**, lưu tại `source_code/server/certs/ca.pem`. Đặt `DATABASE_SSL_CA=certs/ca.pem` trong `.env.shared`. API, Alembic và công cụ nhập dữ liệu đều kiểm tra CA và hostname; không tắt xác thực chứng chỉ.

Nếu cần tạo lại cấu hình, sao chép `.env.example` thành `.env.shared`, điền URL Aiven dạng `mysql+pymysql://USER:PASSWORD@HOST:PORT/defaultdb`, đặt `DATABASE_SSL=true`, `DATABASE_SSL_CA=certs/ca.pem`, `DEBUG=false` và SECRET_KEY riêng. Mã hóa ký tự đặc biệt trong username/password theo URL. Không giữ tham số `ssl-mode` của MySQL CLI trong URL PyMySQL.

## Nhập dữ liệu một lần

Chỉ dùng bản SQL đáng tin cậy của nhóm. Dừng backend trong lúc nhập. **Nhập snapshot trước khi chạy Alembic**: công cụ từ chối mọi database đã có bảng và không ghi đè file uploads có nội dung khác. Nếu Aiven đã có dữ liệu, cần quyết định giữ hay thay thế và sao lưu trước; không tự xóa bảng để chạy công cụ.

Từ gốc repo trên Windows PowerShell:

```powershell
cd source_code/server
# Kiểm tra trước: không ghi database hay uploads.
..\..\.venv\Scripts\python.exe -m scripts.import_shared_data "..\..\..\vieco-data-20261118\vieco-data-20261118"
# Chỉ khi kiểm tra thành công, nhập vào database trống:
..\..\.venv\Scripts\python.exe -m scripts.import_shared_data "..\..\..\vieco-data-20261118\vieco-data-20261118" --apply
# Dùng cùng cấu hình TLS cho Alembic:
$env:VIECO_ENV_FILE='.env.shared'
..\..\.venv\Scripts\python.exe -m alembic upgrade head
Remove-Item Env:VIECO_ENV_FILE
```

Thay đường dẫn snapshot nếu giải nén nơi khác. Công cụ tự lấy `vieco_data.sql` và chép file còn thiếu từ `uploads/company` và `uploads/cvs` vào UPLOAD_DIR. Bản SQL chứa schema và dữ liệu tài khoản, nên không cần seed lại Admin. MySQL DDL không rollback toàn bộ được; nếu nhập lỗi giữa chừng, kiểm tra và khôi phục database trước khi thử lại.

## Chạy trực tiếp trên một máy chung

Từ `source_code/server`:

```powershell
..\..\.venv\Scripts\python.exe run_shared.py
```

Lệnh đọc `.env.shared`, mở website và API tại cổng 8000. Trên máy chủ mở `http://localhost:8000`; các thành viên cùng LAN mở `http://IP-MAY-CHU:8000`. Cho phép cổng 8000 trong firewall cho mạng riêng nếu cần. Máy chủ phải bật và chạy backend thì các thành viên mới dùng được. Đặt FRONTEND_URL trong `.env.shared` thành URL chung thực tế để liên kết email đi đúng website.

Để truy cập qua Internet, triển khai trên máy chủ có ổ đĩa bền vững và reverse proxy HTTPS trỏ tới cổng 8000. URL hosting và quyền triển khai cần do nhóm cung cấp; Aiven chỉ cung cấp database.

## Chạy bằng Docker trên máy chủ

Chuyển code, `.env.shared`, `certs/ca.pem` và **toàn bộ uploads đã nhập** tới đúng vị trí trên máy chủ. Trên máy chủ, từ `source_code`:

```sh
docker compose build
docker compose run --rm web python -m alembic upgrade head
docker compose up -d
docker compose ps
```

Mặc định Docker chỉ mở `127.0.0.1:8000` để reverse proxy HTTPS truy cập. Với mạng LAN, đặt biến môi trường `VIECO_BIND_ADDRESS=0.0.0.0` trước khi chạy Compose. Thư mục `server/uploads` được gắn từ máy chủ vào container, giữ file qua lần dựng lại container. Không đặt thư mục này trên ổ đĩa tạm của hosting. Chỉ chạy một backend với ổ lưu trữ này; nhiều máy backend cần storage chung riêng.

## Xác nhận

- `/api/v1/health`: tiến trình đang chạy; `/api/v1/ready`: HTTP 200 khi truy vấn MySQL thành công, 503 khi lỗi kết nối.
- Mở website trên hai máy và đăng nhập bằng hai tài khoản có sẵn. Thêm/sửa dữ liệu rồi tải lại trang máy còn lại để thấy thay đổi; giao diện không tự đẩy cập nhật nếu chưa tải lại.
- Logo/ảnh công ty mở được; CV tải được qua tài khoản có quyền. Không public thư mục uploads; CV được kiểm tra quyền qua API.
- Nếu trình duyệt từng đặt API riêng, chạy `localStorage.removeItem('vieco_api_base_url')` trong Console rồi tải lại trang.
- Sao lưu cả MySQL và uploads. Không commit `.env.shared`, `ca.pem`, SQL hoặc file dữ liệu cá nhân.

Tài liệu kết nối: [Aiven TLS](https://aiven.io/docs/platform/concepts/tls-ssl-certificates), [SQLAlchemy MySQL TLS](https://docs.sqlalchemy.org/en/20/dialects/mysql.html#ssl-connections).
