# Đưa Vieco lên Render để mọi người truy cập

Hướng dẫn dành cho mã nguồn sau đợt [kiểm tra ngày 18/11/2026](HOSTING_REVIEW_20261118.md), đã được hợp nhất với cấu hình Render trong nhánh `integration/render-release`.

## Hai dịch vụ hiện có của nhóm

Nhóm đã có Static Site `vieco-frontend` tại https://vieco-frontend.onrender.com và backend tại https://vieco.onrender.com. Có thể tiếp tục dùng hai dịch vụ này; xem [các bước triển khai tách frontend/backend](SETUP.md#triển-khai-frontend-trên-render). Bản tích hợp tự chọn backend Render cho Static Site này. Trên backend, đặt `FRONTEND_URL=https://vieco-frontend.onrender.com` và `SERVE_FRONTEND=false`.

Các bước bên dưới mô tả phương án khác: phục vụ cả website và API trên một Web Service với `run_shared.py`. Chỉ chọn phương án này nếu nhóm muốn chạy chung một địa chỉ. Thông tin Aiven và `.env.shared` trong các báo cáo là cấu hình được nhắc tới ở lần kiểm tra trước; cần xác nhận dịch vụ, chứng chỉ và dữ liệu hiện tại trước khi dùng. Việc hợp nhất mã nguồn không xác minh hoặc thay đổi database cloud.

## 1. Chọn cách triển khai

**Người dùng → một website HTTPS trên Render → backend FastAPI → MySQL Aiven.** Ảnh và CV nằm trên ổ đĩa bền vững của backend. Thành viên chỉ cần link website, không cần cài Python hoặc nhận mật khẩu database.

Với cách lưu file hiện tại, chọn **Web Service có gắn Persistent Disk**. Render chỉ cho gắn disk vào dịch vụ trả phí; xem [điều kiện lưu trữ](https://render.com/docs/disks) và [giá hiện hành](https://render.com/pricing) trước khi tạo dịch vụ. Bản miễn phí không có disk bền vững phù hợp cho uploads hiện tại; nếu nhóm bắt buộc miễn phí thì cần thêm tích hợp lưu trữ ngoài cho ảnh/CV trước.

## 2. Đưa bản code đã sửa lên GitHub

Các sửa đổi đang ở máy cục bộ. Review/commit/push hoặc merge PR vào nhánh nhóm chọn triển khai. Render sẽ lấy code từ nhánh đó, không tự lấy file chưa commit trên máy này.

Giữ `.env`, `.env.shared`, `.env.audit`, SQL, ZIP dữ liệu, chứng chỉ và uploads ở ngoài Git. Các file cấu hình riêng đã được ignore. Uploads sẽ được chuyển riêng ở bước 7.

## 3. Chuẩn bị Aiven và dữ liệu

Nhờ người đang quản lý Aiven lấy file CA: **Aiven Console → dịch vụ MySQL → Overview → Connection information → CA Certificate**. Lưu bản cục bộ tại `source_code/server/certs/ca.pem`.

Kết nối của nhóm đã được chuẩn bị trong `.env.shared`. Kiểm tra các giá trị riêng của nhóm, `DATABASE_SSL=true`, `DATABASE_SSL_CA=certs/ca.pem` và SECRET_KEY riêng có ít nhất 32 ký tự. Nếu mật khẩu Aiven đã đổi, cập nhật URL; mã hóa ký tự đặc biệt trong username/password theo URL.

Từ thư mục server trên máy Windows, kiểm tra snapshot trước:

```powershell
..\..\.venv\Scripts\python.exe -m scripts.import_shared_data "..\..\..\vieco-data-20261118\vieco-data-20261118"
```

- Nếu TLS/kết nối lỗi: kiểm tra CA, host/port, mật khẩu và trạng thái Running trên Aiven.
- Nếu báo database đã có bảng: kiểm tra dữ liệu hiện có trước. Công cụ không ghi đè bảng. Nếu đó đã là dữ liệu đúng của nhóm thì giữ nguyên và bỏ qua việc nhập snapshot.
- Nếu báo preflight OK, database trống và nhóm dùng bản snapshot này, thêm `--apply` vào lệnh để nhập. Công cụ cũng chuẩn bị uploads cục bộ.

**Nhập snapshot vào database trống trước khi chạy Alembic**. Sau khi nhập, kiểm tra migration:

```powershell
$env:VIECO_ENV_FILE='.env.shared'
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m alembic current
Remove-Item Env:VIECO_ENV_FILE
```

Kết quả mong đợi: revision `0003`, dữ liệu tài khoản/công ty/tin của nhóm vẫn có. Admin dùng tài khoản trong database; không cần seed lại khi đã nhập snapshot.

## 4. Tạo Web Service trên Render

Mở [Render Dashboard](https://dashboard.render.com/), đăng nhập, chọn **New → Web Service**, kết nối GitHub và chọn repo Vieco. Điền:

| Trường | Giá trị |
| --- | --- |
| Name | Tên tùy chọn, ví dụ `vieco-web` |
| Branch | Nhánh đã chứa bản code được kiểm tra |
| Root Directory | `source_code` |
| Language / Runtime | **Python 3**; chọn rõ Python nếu Render tự nhận Docker |
| Build Command | `pip install -r server/requirements.txt` |
| Start Command | `cd server && python -m alembic upgrade head && python run_shared.py` |
| Health Check Path | `/api/v1/ready` |
| Compute | Gói trả phí hỗ trợ Persistent Disk |

Frontend tĩnh được FastAPI phục vụ cùng API, nên không cần tạo thêm Static Site hoặc chạy npm build. `run_shared.py` tự lắng nghe `0.0.0.0` và cổng PORT do Render cấp. Cách cấu hình dịch vụ tham khảo [Web Services](https://render.com/docs/web-services) và [FastAPI trên Render](https://render.com/docs/deploy-fastapi).

## 5. Thêm biến môi trường và CA

Trong **Environment Variables**, nhập:

| Key | Value |
| --- | --- |
| APP_NAME | `JobContact` |
| DEBUG | `false` |
| DATABASE_URL | URL Aiven riêng của nhóm từ `.env.shared`, dạng `mysql+pymysql://USER:PASSWORD@HOST:PORT/defaultdb` |
| DATABASE_SSL | `true` |
| DATABASE_SSL_CA | `/etc/secrets/ca.pem` |
| SECRET_KEY | Khóa riêng tối thiểu 32 ký tự; có thể dùng khóa đã chuẩn bị trong `.env.shared` |
| UPLOAD_DIR | `/var/data/vieco/uploads` |
| FRONTEND_URL | URL HTTPS của Web Service, cập nhật ngay khi Render cấp tên chính xác |

Trong **Secret Files**, thêm file tên `ca.pem`, dán nguyên nội dung CA đã tải từ Aiven, gồm cả BEGIN CERTIFICATE và END CERTIFICATE. Render cung cấp file đó ở `/etc/secrets/ca.pem` khi chạy. Các mục này nằm trong cấu hình Advanced/Environment của dịch vụ; nếu đã tạo dịch vụ trước khi thêm CA, thêm file và triển khai lại. Xem [Environment Variables and Secrets](https://render.com/docs/configure-environment-variables).

Nếu cần email xác thực/quên mật khẩu/thông báo, thêm SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM, SMTP_STARTTLS và SMTP_SSL theo nhà cung cấp SMTP của nhóm, rồi thử gửi email thật. FRONTEND_URL phải trỏ tới link website chung để email mở đúng trang account.

## 6. Gắn ổ lưu trữ và triển khai

Trong **Advanced → Add Disk** hoặc trang **Disks** của dịch vụ:

- Mount Path: `/var/data/vieco`
- Size: dung lượng nhỏ nhất phù hợp dữ liệu nhóm, có thể bắt đầu 1 GB nếu tùy chọn này được cung cấp.

Giá trị UPLOAD_DIR ở trên nằm trong disk này. Sau khi xác nhận cấu hình và chi phí, tạo/triển khai Web Service. Xem log: Alembic phải hoàn tất, Uvicorn phải khởi động, health check phải đạt. Nếu lỗi TLS hoặc kết nối MySQL, sửa CA/biến môi trường rồi redeploy.

## 7. Chuyển ảnh và CV lên disk

Mở phần **Connect → SSH** trên Render để lấy đúng USER và SSH_HOST của dịch vụ, thiết lập SSH theo hướng dẫn Render. Trên máy cục bộ, từ `source_code/server`, dùng SCP hoặc ứng dụng SFTP để chép **thư mục uploads** vào `/var/data/vieco/`. Ví dụ, thay USER và SSH_HOST bằng thông tin thật Render hiển thị:

```powershell
scp -r ".\uploads" USER@SSH_HOST:/var/data/vieco/
```

Làm việc này trước khi cho mọi người tải file mới lên website. Đích cần có:

```text
/var/data/vieco/uploads/company/...
/var/data/vieco/uploads/cvs/...
```

Chuyển bản uploads đi cùng snapshot/dữ liệu thật, giữ nguyên tên file. Bản uploads thử ở `outputs/hosting-audit` phục vụ kiểm tra cục bộ. Render hướng dẫn chuyển file vào disk tại [Transferring files](https://render.com/docs/disks#transferring-files).

## 8. Kiểm tra rồi gửi link cho nhóm

1. Mở `https://TEN-DICH-VU.onrender.com/api/v1/ready`: cần HTTP 200 và `{"status":"ready"}`.
2. Mở trang chủ: thấy công ty/tin phù hợp dữ liệu Aiven, ảnh tải được.
3. Dùng hai trình duyệt/tài khoản thử các vai trò; tạo/sửa dữ liệu ở một bên, tải lại bên còn lại để thấy dữ liệu chung.
4. Kiểm tra upload/download CV đúng quyền, logo/ảnh công ty, thông báo và email nếu đã bật SMTP.
5. Redeploy một lần; xác nhận ảnh và CV vẫn mở được từ disk.
6. Gửi URL website chung cho nhóm. Lưu kế hoạch sao lưu MySQL và uploads cùng nhau.

Ứng dụng hiện tải lại dữ liệu khi mở/làm mới trang, chưa có WebSocket tự đẩy thay đổi tức thời. HTTPS, SMTP và hành vi trên Linux/Render cần được kiểm chứng bằng các bước này sau khi dịch vụ thực sự được tạo.
