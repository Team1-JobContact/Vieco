# Hướng dẫn chạy dự án Vieco trên Windows

Tài liệu hướng dẫn chạy giao diện, API Python và cơ sở dữ liệu MySQL trên máy cá nhân bằng VS Code và PowerShell.

## 1. Thông tin đã xác định

- Giao diện nằm trong `source_code/client`, trang chính là `index.html`.
- API Python nằm trong `source_code/server`.
- File `source_code/server/run.py` chạy Uvicorn với ứng dụng `src.app:app`, địa chỉ `127.0.0.1`, cổng `8000` và chế độ tự tải lại.
- Backend sử dụng SQLAlchemy và PyMySQL để kết nối MySQL.
- Backend có `requirements.txt`, `.env.example`, `alembic.ini` và thư mục `migrations`.
- `package.json` của client hiện chỉ có script kiểm thử `test`; không có script `start` hoặc `dev`.

**Giới hạn xác minh:** Tài liệu được lập từ cấu trúc và thông báo lỗi đã quan sát. Nội dung `.env.example`, cấu hình Alembic, các route API và README chưa được kiểm tra trực tiếp. Những mục phụ thuộc các file này được ghi rõ bên dưới; không tự thay tên biến hoặc chạy migration khi chưa đối chiếu.

## 2. Chuẩn bị

Cài đặt:

1. Python tương thích với phiên bản thư viện trong `requirements.txt` và hướng dẫn tại README của dự án.
2. MySQL Server, hoặc MySQL trong XAMPP nếu dự án tương thích phiên bản đó.
3. VS Code và extension **Live Server**.
4. Node.js nếu cần chạy các bài kiểm thử JavaScript của client; không bắt buộc để mở HTML bằng Live Server.

Mở thư mục gốc `Vieco` trong VS Code bằng **File → Open Folder**. Mở Terminal qua **Terminal → New Terminal**.

Kiểm tra Python:

```powershell
python --version
python -m pip --version
```

Nếu `python` không được nhận diện, kiểm tra cài đặt Python và PATH. Có thể kiểm tra Python Launcher bằng `py --version`.

## 3. Tạo và sử dụng môi trường Python

Các lệnh dưới đây bắt đầu tại thư mục gốc `Vieco`.

Nếu chưa có thư mục `.venv`, tạo môi trường:

```powershell
python -m venv .venv
```

Có thể dùng trực tiếp Python của môi trường mà không cần kích hoạt:

```powershell
.\.venv\Scripts\python.exe --version
```

Nếu muốn kích hoạt trong PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn `Activate.ps1`, tiếp tục sử dụng đường dẫn đến `python.exe` như trong các bước dưới; không cần thay đổi execution policy.

## 4. Cài thư viện backend

Từ thư mục gốc:

```powershell
cd .\source_code\server
..\..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Chờ lệnh hoàn tất và kiểm tra lỗi trước khi chạy API. Nếu lỗi liên quan phiên bản Python, đối chiếu README và yêu cầu phiên bản của các thư viện, sau đó tạo lại môi trường bằng phiên bản phù hợp.

Không chạy `npm install` tại thư mục gốc để cài backend Python.

## 5. Khởi động MySQL

Chọn cách tương ứng với phần mềm đã cài:

### MySQL cài riêng

1. Nhấn `Win + R`, nhập `services.msc`.
2. Tìm dịch vụ MySQL; tên có thể là `MySQL`, `MySQL80`, `MySQL84` hoặc tên khác do lúc cài đặt đặt ra.
3. Chọn **Start** nếu dịch vụ chưa chạy.

### XAMPP

1. Mở XAMPP Control Panel.
2. Chọn **Start** ở dòng MySQL.
3. Kiểm tra cổng thực tế trong cấu hình nếu không dùng cổng mặc định.

Chỉ chạy một dịch vụ cơ sở dữ liệu trên cùng một cổng. Không khởi động đồng thời MySQL riêng và MySQL của XAMPP nếu cả hai dùng chung cổng.

Kiểm tra cổng bằng PowerShell, thay `3306` nếu cấu hình của bạn khác:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 3306
```

`TcpTestSucceeded: True` chỉ xác nhận có dịch vụ nhận kết nối TCP; chưa xác nhận tài khoản, mật khẩu hoặc database đúng.

## 6. Cấu hình backend và database

Tại `source_code/server`, nếu chưa có `.env`, sao chép file mẫu:

```powershell
Copy-Item .env.example .env
```

Nếu `.env` đã tồn tại, mở và đối chiếu với `.env.example`; không ghi đè cấu hình đang có.

Điền đúng tên biến mà file mẫu và mã nguồn đang sử dụng. Các giá trị cần kiểm tra thường gồm:

| Thông tin | Giá trị cần xác định |
| --- | --- |
| Host MySQL | `127.0.0.1` hoặc địa chỉ máy chủ thực tế |
| Port MySQL | Thường là `3306`; dùng cổng thực tế |
| Database | Tên database dự án yêu cầu |
| Username | Tài khoản MySQL có quyền trên database |
| Password | Mật khẩu của tài khoản trên |
| Cấu hình khác | Các biến bắt buộc khác trong `.env.example` |

Nếu dự án dùng một chuỗi kết nối SQLAlchemy cho PyMySQL, dạng thường gặp là:

```text
mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/DATABASE
```

Đây chỉ là ví dụ định dạng, không phải tên biến hoặc thông tin đăng nhập đã xác minh của Vieco. Nếu mật khẩu có ký tự đặc biệt và được đưa vào URL, cần mã hóa thành phần mật khẩu đúng định dạng URL hoặc dùng cơ chế cấu hình mà dự án cung cấp.

Không công khai `.env`, mật khẩu hoặc khóa bí mật.

### Tạo database và cấu trúc bảng

Đọc `README.md`, `source_code/README.md`, `alembic.ini` và hướng dẫn trong `migrations` để biết tên database và cách khởi tạo chính thức.

Nếu cần tạo database thủ công, có thể dùng MySQL Workbench hoặc công cụ quản trị đang sử dụng. Câu SQL minh họa dưới đây phải được thay bằng tên database đúng trong cấu hình:

```sql
CREATE DATABASE ten_database_du_an CHARACTER SET utf8mb4;
```

Nếu README xác nhận dự án quản lý schema bằng Alembic, chạy tại `source_code/server` sau khi cấu hình database:

```powershell
..\..\.venv\Scripts\python.exe -m alembic upgrade head
```

Lệnh này thay đổi cấu trúc database. Chỉ chạy sau khi xác nhận database đích là database phát triển của bạn và cấu hình Alembic đã đúng. Nếu dự án yêu cầu import SQL hoặc cơ chế khởi tạo khác, làm theo hướng dẫn đó. Sự hiện diện của thư mục `prisma` không đủ để kết luận phải chạy Prisma song song với Alembic.

Nếu có bước seed dữ liệu hoặc tạo tài khoản mẫu, dùng lệnh được ghi trong README. Không giả định đã có tài khoản mẫu hoặc tự đoán mật khẩu.

## 7. Chạy API

Tại `source_code/server`:

```powershell
..\..\.venv\Scripts\python.exe run.py
```

Nếu đã kích hoạt đúng `.venv`, cũng có thể dùng:

```powershell
python run.py
```

Theo `run.py`, địa chỉ API là:

```text
http://127.0.0.1:8000
```

Chờ thông báo `Application startup complete` và kiểm tra không có traceback làm ứng dụng khởi động thất bại. Giữ Terminal này mở.

Nếu ứng dụng bật trang tài liệu API theo cấu hình FastAPI thông thường, thử mở `http://127.0.0.1:8000/docs`. Nếu nhận 404, kiểm tra cấu hình route trong `src/app.py`; không kết luận máy chủ hỏng chỉ vì đường dẫn `/` hoặc `/docs` trả 404.

## 8. Kết nối giao diện với API

Trong VS Code, dùng `Ctrl + Shift + F`, giới hạn tìm trong `source_code/client` và tìm:

- `8000`
- `localhost`
- `127.0.0.1`
- `API_BASE_URL`
- `fetch(`

Xác định nơi khai báo địa chỉ backend và đối chiếu với `http://127.0.0.1:8000`. Giữ đúng tiền tố đường dẫn của dự án, chẳng hạn `/api` nếu mã nguồn có sử dụng; không tự thêm hoặc bỏ tiền tố.

Nếu mã nguồn gọi đường dẫn tương đối như `/api/...`, kiểm tra README xem có cần proxy hoặc phục vụ frontend qua backend hay không. Live Server không tự chuyển các yêu cầu đó đến cổng 8000.

Để mở giao diện bằng Live Server:

1. Mở `source_code/client/index.html`.
2. Nhấp chuột phải → **Open with Live Server**.
3. Ghi nhận địa chỉ thực tế trên trình duyệt, ví dụ `http://127.0.0.1:5500` cùng đường dẫn trang.
4. Mở trang nhà tuyển dụng, đăng nhập hoặc đăng ký từ giao diện.

Không mở HTML bằng đường dẫn `file://` khi cần gọi API.

### Nếu gặp CORS

Mở DevTools bằng `F12`, xem **Console** và **Network**. Nếu trình duyệt báo CORS, tìm cấu hình CORS của backend và thêm đúng origin frontend đang dùng theo cơ chế cấu hình của dự án.

Ví dụ, `http://localhost:5500` và `http://127.0.0.1:5500` là hai origin khác nhau. Nếu sử dụng cookie hoặc thông tin xác thực, cần cấu hình origin cụ thể và chế độ credentials phù hợp; không mặc định dùng `*`.

Khởi động lại backend sau khi sửa cấu hình `.env` hoặc cấu hình kết nối khi cần.

## 9. Kiểm tra chạy hoàn chỉnh

Thực hiện với database phát triển và dữ liệu thử:

1. MySQL đang chạy và cổng database nhận kết nối.
2. Backend khởi động xong, không còn lỗi kết nối hoặc thiếu bảng.
3. Frontend mở bằng HTTP qua Live Server hoặc cách phục vụ được README chỉ định.
4. Trong **F12 → Network**, tải lại trang và kiểm tra URL API gọi đúng host, port và đường dẫn.
5. Thử đăng ký tài khoản thử, đăng nhập và tải dữ liệu theo các chức năng dự án hỗ trợ.
6. Kiểm tra dữ liệu thử được lưu vào đúng database khi chức năng yêu cầu lưu trữ.

Tham khảo thêm `docs/TEST_CHECKLIST.md` để kiểm tra các chức năng theo checklist của dự án.

## 10. Các lỗi thường gặp

| Hiện tượng | Cách kiểm tra và xử lý |
| --- | --- |
| `npm error enoent` tại thư mục gốc | Đang chạy npm ở nơi không có `package.json`. Backend chạy bằng Python; client chỉ cần npm khi chạy kiểm thử. |
| `ModuleNotFoundError` | Cài `requirements.txt` bằng chính Python của `.venv`, rồi chạy backend bằng Python đó. |
| MySQL lỗi `2003`, `WinError 10061` | Kiểm tra MySQL đã chạy, host và port trong cấu hình đúng. Đây là lỗi kết nối bị từ chối, chưa phải bằng chứng mật khẩu sai. |
| MySQL `Access denied` | Kiểm tra username, password và quyền của tài khoản đối với host/database. |
| `Unknown database` | Kiểm tra tên database; tạo database đúng theo README nếu chưa có. |
| Thiếu bảng hoặc cột | Kiểm tra đã áp dụng migration hoặc import schema theo hướng dẫn dự án. |
| Cổng 8000 đang được sử dụng | Kiểm tra có backend đang chạy ở Terminal khác không. Dừng đúng tiến trình của dự án hoặc đổi cổng và cập nhật cấu hình frontend tương ứng. |
| Giao diện báo không kết nối được API | Xem Network để phân biệt URL sai, backend chưa chạy, CORS hoặc lỗi HTTP từ server. |
| HTTP 404 ở API | Kiểm tra route, tiền tố `/api` và phương thức gọi. |
| HTTP 401/403 | Kiểm tra đăng nhập và quyền truy cập. |
| HTTP 500 | Đọc traceback trong Terminal backend để xác định nguyên nhân. |

Khi cần hỗ trợ, gửi lệnh vừa chạy, traceback liên quan, URL request và mã trạng thái HTTP. Che mật khẩu, token và dữ liệu cá nhân.

## 11. Chạy kiểm thử client khi cần

Mở Terminal mới từ thư mục gốc:

```powershell
cd .\source_code\client
npm ci
npm test
```

`npm ci` sử dụng `package-lock.json` hiện có. Kiểm thử client không thay thế việc kiểm tra backend và database đang hoạt động.

## 12. Các lần chạy tiếp theo

Sau khi đã cài thư viện, cấu hình `.env` và khởi tạo database:

1. Khởi động MySQL.
2. Mở Terminal tại thư mục gốc `Vieco` và chạy:

```powershell
cd .\source_code\server
..\..\.venv\Scripts\python.exe run.py
```

3. Mở `source_code/client/index.html` bằng Live Server.
4. Tải lại trang sau khi backend khởi động xong.

Dừng API bằng `Ctrl + C` trong Terminal. Dừng Live Server bằng nút **Port** trên thanh trạng thái VS Code. Chỉ dừng dịch vụ MySQL khi không còn ứng dụng khác cần sử dụng.
