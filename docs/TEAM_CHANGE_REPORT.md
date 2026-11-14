# Báo cáo thay đổi và bàn giao trước khi merge main

Ngày cập nhật: 15/11/2026. Nhánh đề xuất: `feat/architecture-api-alignment`. Nhánh đích: `main`. Trạng thái tại thời điểm lập báo cáo: mã nguồn đã đẩy lên GitHub, chưa merge vào main.

Bản cập nhật bổ sung biểu mẫu nhà tuyển dụng, nối với API tuyển dụng, tổ chức lại mã nguồn và triển khai các API còn thiếu theo thiết kế JobContact. Thành viên cần cập nhật đường dẫn file khi tiếp tục phát triển và kiểm tra luồng công ty → tin tuyển dụng → ứng tuyển trên môi trường dùng chung trước khi nghiệm thu.

## 1. Phạm vi bàn giao

Báo cáo tính từ `main` tại commit `6f22a6c` đến mã nguồn tại commit `177d5f1`, bao gồm cả các commit tiền nhiệm của nhánh. Vì vậy đây là thay đổi tổng hợp, không chỉ là đổi cấu trúc thư mục hoặc riêng task PB-015. Các commit tài liệu bàn giao sau `177d5f1` chỉ cập nhật nội dung hướng dẫn/báo cáo.

| Nhóm thay đổi | Kết quả bàn giao |
| --- | --- |
| PB-015 và tích hợp PB-014 | Giao diện tạo/sửa hồ sơ công ty, tạo/sửa/gửi duyệt tin; gọi API thật; sửa hành vi PATCH để giữ dữ liệu không gửi lên |
| Tổ chức mã nguồn | Frontend gom theo tính năng và HTTP service; backend tách routes, controllers, services, models và auth middleware |
| API theo thiết kế | Có đủ 24 cặp method/đường dẫn cốt lõi trong Word; giữ các API cũ để tương thích |
| Giao diện công khai và tài khoản | Trang chủ lấy việc làm thật, tìm kiếm/phân trang/chi tiết; thêm trang xác thực email và đặt lại mật khẩu |
| Email và phiên đăng nhập | Thêm SMTP, token xác thực/reset dùng một lần; phiên cũ mất hiệu lực sau reset |
| Tài liệu và kiểm thử | Bổ sung báo cáo đối chiếu, sơ đồ thư mục, hướng dẫn vận hành và test nghiệp vụ/UI |

Công nghệ tiếp tục là HTML/CSS/JavaScript, FastAPI, SQLAlchemy, Alembic và MySQL. Bản Word yêu cầu React/Vite/Tailwind, Express và Prisma; khác biệt này được ghi nhận trong [báo cáo kiến trúc](ARCHITECTURE_REVIEW.md). Nhóm cần thống nhất với người duyệt thiết kế nếu framework là tiêu chí nghiệm thu bắt buộc.

## 2. Thay đổi người dùng có thể thấy

Nhà tuyển dụng có trang `pages/employer.html`: tạo/sửa hồ sơ công ty, xem trạng thái/lý do từ chối và gửi lại hồ sơ bị từ chối. Công ty phải được Admin duyệt trước khi quản lý tin tuyển dụng. Chủ sở hữu công ty được sửa hồ sơ; thành viên MEMBER chỉ xem phần hồ sơ công ty trong giao diện này.

Biểu mẫu tin hỗ trợ lưu nháp, mở tin bằng `?job_id=<id>#job`, sửa nháp/tin bị từ chối và gửi duyệt. Form giữ dữ liệu khi lỗi, khóa thao tác đang gửi và cảnh báo khi rời trang có thay đổi chưa lưu. Dữ liệu danh mục lấy từ database, không dùng ID hardcode.

Trang chủ hiển thị tin đã duyệt, công ty đã duyệt, tin còn hạn và chưa bị gỡ. Người xem có thể tìm theo tiêu đề, chuyển trang và mở chi tiết. Lượt xem tăng khi gọi API chi tiết. Danh sách rỗng có thể do chưa có tin đủ điều kiện, không đồng nghĩa API mất kết nối.

Trang đăng nhập/đăng ký có liên kết Quên mật khẩu. Trang `pages/account.html` nhận liên kết xác thực email/đặt lại mật khẩu do SMTP gửi. Trang quản trị Admin, giao diện ứng viên ứng tuyển và giao diện thông báo đầy đủ chưa được bàn giao trong đợt này; các nghiệp vụ đó hiện thao tác qua API/Swagger.

## 3. Đường dẫn cần dùng khi phát triển tiếp

Bảng sau so sánh trực tiếp với main tại `6f22a6c`; các đường dẫn trong giai đoạn refactor trung gian xem [PROJECT_STRUCTURE](PROJECT_STRUCTURE.md).

| Trên main trước cập nhật | Trên nhánh bàn giao |
| --- | --- |
| client/assets/css/auth.css, style.css | client/src/assets/css/auth.css, style.css |
| client/assets/js/auth-api.js | client/src/services/auth-api.js |
| client/assets/js/auth-ui.js | client/src/features/auth/auth-ui.js |
| client/assets/js/main.js | client/src/features/jobs/home-ui.js; danh sách việc làm gọi src/services/jobs-api.js |
| Chưa có biểu mẫu nhà tuyển dụng trong main | client/pages/employer.html; src/features/employer/employer-ui.js; src/services/employer-api.js |
| Chưa có trang khôi phục tài khoản | client/pages/account.html; src/features/auth/account-ui.js; src/services/account-api.js |
| server/src/routes/*.py chứa cả handler | routes khai báo URL/response; handler chuyển sang controllers/*_controller.py |
| server/src/middlewares/auth.py | Vẫn dùng đường dẫn này cho mã mới; dependencies/auth.py re-export để tương thích giai đoạn refactor |
| Các file khung Express/Prisma | Giữ trong archive/, không dùng để chạy backend hiện tại |

Backend tiếp nhận request theo luồng `routes → controllers → services → models`. Request/response Pydantic nằm trong `schemas`; cấu hình database/SMTP nằm trong `config`; JWT/bcrypt nằm trong `utils`. Giữ nghiệp vụ và transaction trong service khi thêm API; UI gọi HTTP qua các file service để tránh rải URL ở nhiều nơi.

## 4. API và hợp đồng tích hợp cần lưu ý

Base URL vẫn là `http://127.0.0.1:8000/api/v1`. Request cần xác thực sử dụng `Authorization: Bearer <token>`. Swagger tại `http://127.0.0.1:8000/docs` thể hiện schema thực tế. Danh sách 24 endpoint và quyền truy cập chi tiết nằm trong [ARCHITECTURE_REVIEW](ARCHITECTURE_REVIEW.md).

| Phần tích hợp | Hành vi cần biết |
| --- | --- |
| GET /categories | Trả industries, provinces và thêm skills; chỉ bản ghi đang hoạt động. Client không nên so sánh cứng toàn bộ object với schema cũ có hai khóa |
| POST/PATCH tin tuyển dụng | POST hỗ trợ action draft/submit; PATCH phân biệt không gửi trường với gửi null; trường không gửi giữ nguyên, null chỉ dùng để xóa giá trị tùy chọn |
| GET/PUT /users/profile | GET trả thông tin tài khoản kèm profile nếu có; PUT chỉ cho ứng viên, tạo profile nếu chưa có và cập nhật các trường gửi lên |
| PATCH /admin/companies/{id}/approval | Duyệt/từ chối hồ sơ công ty; body status APPROVED hoặc REJECTED |
| PATCH /admin/jobs/{id}/approval | Duyệt/từ chối tin riêng biệt với công ty; cùng body status |
| POST /applications | Chọn job_id, cv_id, cover_letter tùy chọn; CV phải thuộc ứng viên và chưa bị xóa; chặn đơn trùng |
| API đơn của nhà tuyển dụng | Chỉ xem/đổi trạng thái đơn thuộc tin của công ty mình; mỗi lần đổi có lịch sử và thông báo |
| GET /notifications, PATCH /notifications/{id}/read | Chỉ dữ liệu của người đăng nhập; đánh dấu đọc lại giữ nguyên thời điểm đọc đầu |

Ví dụ duyệt hoặc từ chối:

```json
{"status":"APPROVED"}
```

```json
{"status":"REJECTED","reason":"Thông tin chưa đầy đủ, cần bổ sung mô tả công việc"}
```

Lý do từ chối phải từ 10 đến 500 ký tự. Admin không tự đăng ký qua API register; dùng tài khoản Admin đã được seed. Không dùng token EMPLOYER để gọi API Admin. API employer/candidate và các endpoint approve/reject cũ vẫn được giữ cho tích hợp hiện có.

## 5. Trạng thái cần hiểu thống nhất

Với tin tuyển dụng, `DRAFT` là bản nháp, chưa gửi duyệt; thao tác gửi duyệt chuyển sang `PENDING`. Admin duyệt thành công chuyển sang `APPROVED`. Chỉ duyệt công ty không tự duyệt các tin của công ty đó. Tin đã duyệt có thể chuyển về PENDING khi sửa nội dung chính qua API; giao diện nhà tuyển dụng hiện chủ yếu cho sửa nháp/tin bị từ chối.

```text
DRAFT → gửi duyệt → PENDING → Admin duyệt → APPROVED
                         └→ Admin từ chối → REJECTED → sửa và gửi lại → PENDING
```

Vòng đời tin còn có CLOSED/EXPIRED theo nghiệp vụ sẵn có; sơ đồ trên chỉ minh họa phần gửi duyệt. API công khai tiếp tục lọc hạn nộp ngay cả khi bản ghi chưa chuyển trạng thái EXPIRED.

Với đơn ứng tuyển, triển khai hiện áp dụng NEW → VIEWED/INTERVIEW/REJECTED; VIEWED → INTERVIEW/REJECTED; INTERVIEW → ACCEPTED/REJECTED. Ứng viên chỉ rút đơn ở NEW/VIEWED, chuyển sang WITHDRAWN. Quy tắc chuyển trạng thái này cần được nhóm xác nhận khi rà soát SRS vì bản Word kiến trúc không mô tả đầy đủ các bước chuyển.

## 6. Cấu hình và dữ liệu khi cập nhật

Cổng backend là 8000, frontend là 5500; URL trang và cách chạy giữ nguyên. Mỗi thành viên giữ `.env` riêng tại `source_code/server/.env`, kiểm tra DATABASE_URL và SECRET_KEY của máy mình. Không chép đè `.env` đang dùng bằng `.env.example`. `GET /health` chỉ kiểm tra API đang chạy, không xác nhận database kết nối thành công.

Để dùng email, bổ sung các biến từ [file mẫu](../source_code/server/.env.example): SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM, SMTP_STARTTLS, SMTP_SSL và FRONTEND_URL. FRONTEND_URL phải trỏ tới frontend đang phục vụ trang account, mặc định `http://localhost:5500`.

| Tình huống | Hành vi hiện tại |
| --- | --- |
| Chưa cấu hình SMTP | Đăng ký vẫn hoạt động, không gửi xác thực; forgot-password trả 503 |
| Có SMTP | Xác thực có hạn 24 giờ; reset 30 phút; token lưu băm SHA-256, chỉ dùng một lần |
| Reset mật khẩu thành công | Các JWT cũ bị từ chối; người dùng cần đăng nhập lại |
| Email thông báo sự kiện gửi lỗi | Ghi FAILED; nghiệp vụ đã commit vẫn giữ kết quả |
| Email xác thực lúc đăng ký gửi lỗi | Tài khoản vẫn tồn tại; chưa có API gửi lại xác thực |

Hiện chưa bắt buộc xác thực email trước khi đăng nhập. Gửi email sự kiện đang đồng bộ sau commit, chưa có hàng đợi bền vững hay tự thử lại. Không thay đổi schema/revision Alembic so với main trong phạm vi bàn giao này; không có migration mới riêng cho bản cập nhật. Máy mới hoặc database chưa được khởi tạo vẫn cần làm theo [SETUP](SETUP.md), không được bỏ qua migration/seed ban đầu.

`.env`, môi trường ảo, node_modules và dữ liệu uploads cục bộ được Git bỏ qua; uploads chỉ giữ `.gitkeep`. Thành viên cần tự chuẩn bị database/tệp CV trên máy của mình; Git pull không mang theo những dữ liệu này.

## 7. Kết quả kiểm thử và giới hạn

Kết quả đã ghi nhận trên mã nguồn trước commit tài liệu bàn giao:

| Kiểm tra | Kết quả |
| --- | --- |
| Backend pytest | 52 passed; 2 cảnh báo deprecation có sẵn |
| Frontend Node/jsdom | 21 passed |
| Đối chiếu bảng Word với OpenAPI | 24/24 cặp method/URL; có test đọc trực tiếp file Word |
| Đường dẫn HTML nội bộ | 51 tham chiếu tồn tại |
| Cú pháp và whitespace | Python/JavaScript hợp lệ; git diff --check đạt |
| Mô phỏng merge với main 6f22a6c | Không có conflict Git; main là tổ tiên của nhánh mã nguồn |

Backend test dùng SQLite, SMTP dùng transport giả lập và UI được kiểm tra bằng jsdom. Chưa có kết quả xác minh MySQL thật, SMTP thật, giao diện trình duyệt thật, HTTPS hay hiệu năng tải. Chưa triển khai upload logo riêng. Đủ đường dẫn API và merge không conflict không đồng nghĩa đã hoàn thành toàn bộ SRS hoặc đủ điều kiện nghiệm thu hệ thống.

## 8. Các việc nhóm cần kiểm tra trước khi merge

Các mục dưới đây là đề xuất phân chia theo phần việc; nhóm tự xác nhận người phụ trách, không phải phân công đã được các thành viên nhận.

| Phần việc | Cần kiểm tra |
| --- | --- |
| Frontend | URL JS/CSS mới, đăng nhập/đăng xuất, form công ty/tin, tìm kiếm/phân trang, trang account trên trình duyệt thật và màn hình nhỏ |
| M0 danh mục/cấu hình | industries/provinces/skills, quyền thêm danh mục của Admin, dữ liệu seed trên database phát triển |
| M1 tài khoản/hồ sơ | Vai trò, profile/CV, email xác thực/reset, token cũ sau reset; thống nhất có bắt buộc xác thực email không |
| M2 tuyển dụng/ứng tuyển | Duyệt công ty và tin độc lập, PATCH không mất dữ liệu, đơn trùng, CV của người khác, quyền công ty và quy tắc trạng thái đơn |
| M3 thông báo/email | Chỉ thấy thông báo của mình, đánh dấu đọc, SMTP thành công/thất bại, thống nhất phương án gửi lại khi lỗi |
| Người tích hợp | Kiểm tra diff/PR, cập nhật main mới nhất và mô phỏng merge lại nếu main thay đổi |

Checklist kiểm tra trên môi trường dùng chung:

- [ ] Chạy backend với MySQL phát triển; kiểm tra Swagger và API danh mục thực sự đọc được database.
- [ ] Nhà tuyển dụng tạo công ty; Admin duyệt công ty bằng đúng ID.
- [ ] Lưu tin DRAFT, gửi thành PENDING, Admin duyệt thành APPROVED; tin đủ điều kiện xuất hiện ở trang chủ.
- [ ] Thử tài khoản sai vai trò và tài khoản thuộc công ty khác; xác nhận bị chặn.
- [ ] Ứng viên tạo profile/upload CV, nộp đơn; thử đơn trùng/CV không thuộc mình; kiểm tra lịch sử và thông báo.
- [ ] Kiểm tra luồng rút đơn, phỏng vấn, nhận/từ chối theo quy tắc nhóm đã thống nhất.
- [ ] Cấu hình SMTP thử nghiệm; mở email xác thực/reset từ liên kết, kiểm tra hết hạn/dùng lại token và đăng nhập lại sau reset.
- [ ] Xác nhận yêu cầu công nghệ với người duyệt thiết kế và ghi nhận phần UI/chức năng còn thiếu.
- [ ] Review thay đổi và merge sau khi các mục cần thiết được nhóm chấp nhận.

## 9. Cập nhật mã nguồn trên máy thành viên

Trước khi đổi nhánh/pull, lưu công việc đang làm bằng commit hoặc stash của chính mình và kiểm tra `git status`. Để xem trước bản cập nhật, dùng nhánh `feat/architecture-api-alignment` trên GitHub. Sau khi nhánh đã được merge, cập nhật main:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
```

Nếu main cục bộ có commit riêng và pull --ff-only dừng lại, cần xử lý lịch sử với người tích hợp; không dùng reset để bỏ thay đổi. Các nhánh tính năng cũ cần đồng bộ và sửa đường dẫn theo mục 3, tránh tạo lại file ở vị trí đã di chuyển.

Chạy trong terminal thứ nhất, bắt đầu tại gốc repository có môi trường ảo đã cài dependency:

```powershell
cd source_code/server
..\..\.venv\Scripts\python.exe run.py
```

Chạy trong terminal thứ hai, cũng bắt đầu tại gốc repository:

```powershell
cd source_code/client
..\..\.venv\Scripts\python.exe -m http.server 5500
```

Mở `http://localhost:5500`; Swagger là `http://127.0.0.1:8000/docs`. Frontend không cần npm build. `npm ci` tại client phục vụ cài dependency kiểm thử; chạy `npm test` tại client và `python -m pytest tests -q` tại server bằng Python của môi trường ảo. Hướng dẫn cài mới đầy đủ nằm trong [SETUP](SETUP.md).

## 10. Tài liệu để đọc tiếp

- [Cấu trúc thư mục và trách nhiệm từng lớp](PROJECT_STRUCTURE.md).
- [Đối chiếu công nghệ và 24 endpoint với bản thiết kế](ARCHITECTURE_REVIEW.md).
- [Chi tiết biểu mẫu nhà tuyển dụng và hợp đồng tích hợp PB-015](PB-015.md).
- [Hướng dẫn cài đặt](SETUP.md).
- [Nội dung thông báo ngắn để gửi nhóm](TEAM_ANNOUNCEMENT.md).
