# Đối chiếu thiết kế hệ thống JobContact

Ngày rà soát: 15/11/2026. Trạng thái: đã đẩy mã nguồn lên nhánh `feat/architecture-api-alignment`, chưa merge vào `main`.

Báo cáo này tập trung vào đợt chỉnh kiến trúc từ nền mã trước refactor; phạm vi toàn bộ nhánh so với main, tác động đến từng phần việc và checklist bàn giao xem [TEAM_CHANGE_REPORT](TEAM_CHANGE_REPORT.md).

Nguồn: [bản thiết kế Word](JobContact_System_Architecture_and_APIs.docx), đã được đối chiếu SHA-256 trùng với bản thiết kế tham chiếu khi rà soát.

## Kết luận và quyết định

Dự án ban đầu chưa khớp bản thiết kế: frontend dùng HTML/CSS/JavaScript thay React/Vite/Tailwind; backend dùng FastAPI/SQLAlchemy/Alembic thay Express/Prisma; chỉ 3 trong 24 endpoint cốt lõi có đúng method và đường dẫn. Một số nghiệp vụ đã tồn tại tại API employer/candidate, nhưng chưa có đường dẫn chuẩn trong bản Word.

Phương án triển khai trong đợt này giữ nền tảng hiện có để tận dụng nghiệp vụ và kiểm thử đã xây dựng. Đã tổ chức lại phân lớp và bổ sung đủ đường dẫn API cốt lõi. **Chưa khớp 100% công nghệ và cây thư mục React/Express trong Word.** Nếu tài liệu này là tiêu chí nghiệm thu bắt buộc về framework, cần một đợt chuyển đổi riêng hoặc thống nhất cập nhật tài liệu thiết kế với nhóm.

## Công nghệ và kiến trúc

| Yêu cầu Word | Mã nguồn sau chỉnh sửa | Đánh giá |
| --- | --- | --- |
| Client–Server, REST JSON, JWT Bearer | Frontend tách server, /api/v1, JWT Bearer | Tương ứng |
| React SPA, Vite, Tailwind | HTML pages, JS theo tính năng, CSS hiện có | Khác có chủ đích |
| Express, controllers/routes/services | FastAPI với routes/controllers/services/models | Tương ứng phân lớp; khác framework |
| MySQL, Prisma | MySQL, SQLAlchemy, Alembic | Đúng hệ CSDL; khác ORM/migration |
| JWT + bcrypt, RBAC | JWT + bcrypt, auth dependency, vai trò ADMIN/CANDIDATE/EMPLOYER | Có triển khai và kiểm thử |
| Multer, CV PDF/DOC/DOCX tối đa 5 MB | UploadFile, cv_service; kiểm tra kích thước/định dạng/quyền | Tương ứng CV; chưa có luồng upload logo riêng |
| Nodemailer SMTP, xác thực và sự kiện | smtplib SMTP, email_service, trạng thái gửi thông báo | Cần SMTP thật để xác minh vận hành |
| Snake_case, bảng số nhiều | Giữ schema hiện tại | Phần lớn phù hợp; application_status_history là tên cũ số ít, chưa đổi schema |
| HTTPS | Chạy HTTP cục bộ | TLS do triển khai/proxy cấu hình, chưa kiểm chứng |

## Đối chiếu 24 endpoint cốt lõi

Tất cả đường dẫn sau có tiền tố `/api/v1`. `{id}` biểu diễn path parameter như `:id` trong Word. Cột “Trước” phản ánh thời điểm bắt đầu rà soát; “Sau” là mã đã triển khai, chưa đồng nghĩa mọi tích hợp ngoài đã kiểm chứng trên môi trường thật.

| Method và đường dẫn | Trước | Sau |
| --- | --- | --- |
| POST /auth/register | Có | Giữ; thêm gửi xác thực nếu cấu hình SMTP |
| POST /auth/verify-email | Thiếu | Token băm, hết hạn, chỉ dùng một lần |
| POST /auth/login | Có | Giữ JWT + bcrypt |
| POST /auth/forgot-password | Thiếu | Gửi link SMTP; phản hồi chung cho email không tồn tại |
| POST /auth/reset-password | Thiếu | Đổi mật khẩu; phiên cũ mất hiệu lực |
| GET /users/profile | /auth/me và /candidates/me/profile | Thông tin tài khoản kèm profile nếu có |
| PUT /users/profile | PATCH /candidates/me/profile | Chỉ ứng viên; tạo profile nếu chưa có, cập nhật trường gửi lên |
| GET /categories | Có ngành và tỉnh | Bổ sung kỹ năng; chỉ danh mục đang hoạt động |
| POST /admin/categories | Thiếu | Admin thêm ngành/kỹ năng/tỉnh, kiểm tra trùng và liên kết |
| POST /companies | POST /employer/company | Tái sử dụng service tạo công ty chờ duyệt |
| GET /companies/{id} | Thiếu | Chỉ công ty APPROVED, không trả thông tin kiểm duyệt nội bộ |
| PATCH /admin/companies/{id}/approval | POST approve/reject riêng | Body status APPROVED/REJECTED; từ chối cần reason |
| GET /jobs | Thiếu | Công khai tin còn hạn, đã duyệt, công ty đã duyệt; tìm kiếm/lọc/phân trang |
| GET /jobs/{id} | Chỉ employer/admin | Chi tiết công khai và tăng lượt xem |
| POST /jobs | POST /employer/jobs | Giữ nghiệp vụ nháp/gửi duyệt, yêu cầu công ty đã duyệt |
| PATCH /jobs/{id} | PATCH /employer/jobs/{id} | Giữ kiểm tra chủ sở hữu và quy trình duyệt lại |
| PATCH /admin/jobs/{id}/approval | POST approve/reject riêng | Dùng cùng service và quy tắc duyệt hiện có |
| POST /applications | Có model, chưa có API | CV thuộc ứng viên, tin còn nhận đơn, không ứng tuyển trùng |
| GET /applications/my-applications | Thiếu | Chỉ dữ liệu của ứng viên hiện tại, phân trang |
| PATCH /applications/{id}/withdraw | Thiếu | Kiểm tra sở hữu và trạng thái, ghi lịch sử |
| GET /employer/jobs/{jobId}/applications | Thiếu | Chỉ đơn thuộc tin của công ty mình |
| PATCH /applications/{id}/status | Thiếu | Kiểm tra công ty, chuyển trạng thái, lịch sử và thông báo |
| GET /notifications | Có model, chưa có API | Chỉ thông báo của người đăng nhập, phân trang |
| PATCH /notifications/{id}/read | Thiếu | Chỉ chủ thông báo; đọc lại không đổi read_at |

API cũ vẫn được giữ để giao diện và tích hợp đang có hoạt động. Hợp đồng payload/response chi tiết xem Swagger tại `/docs`; Word chỉ nêu method, URL, mô tả và quyền nên các trường bổ sung là quyết định triển khai, không phải trích nguyên đặc tả Word.

Ví dụ duyệt: `{"status":"APPROVED"}` hoặc `{"status":"REJECTED","reason":"Lý do tối thiểu 10 ký tự"}`. Tạo danh mục: `{"type":"skills","name":"Python","industry_id":1}`; tỉnh cần `code`. Tạo đơn: `{"job_id":1,"cv_id":1,"cover_letter":"..."}`. Reset: `{"token":"...","password":"NewPass123"}`.

Quy tắc đơn hiện áp dụng: NEW → VIEWED/INTERVIEW/REJECTED; VIEWED → INTERVIEW/REJECTED; INTERVIEW → ACCEPTED/REJECTED. Ứng viên rút đơn ở NEW/VIEWED. Bản Word không mô tả chi tiết các bước chuyển này; cần đối chiếu SRS khi thay đổi quy tắc nghiệp vụ.

## Giao diện và email

Trang chủ bỏ dữ liệu việc làm mẫu, dùng API danh sách/chi tiết thật, có tìm kiếm và phân trang. Trang `pages/account.html` xử lý liên kết xác thực email/đặt lại mật khẩu; có liên kết Quên mật khẩu ở trang auth. Các UI nằm trong `src/features`, HTTP client trong `src/services`, CSS trong `src/assets`.

SMTP cấu hình theo `.env.example`. Xác thực email có hạn 24 giờ; reset 30 phút; token lưu băm SHA-256. Không trả token trong API. Sau reset, JWT cũ bị từ chối. Khi chưa cấu hình SMTP, đăng ký vẫn hoạt động như trước, không gửi email; forgot-password trả 503. Hiện không bắt buộc xác thực email trước khi đăng nhập để giữ hành vi cũ; nếu SRS yêu cầu chặn tài khoản chưa xác thực, cần bật quy tắc riêng và luồng gửi lại xác thực.

Sự kiện duyệt công ty/tin, tạo đơn và đổi trạng thái đơn gửi SMTP khi đã cấu hình. Lỗi SMTP ghi email_status=FAILED, không hoàn tác nghiệp vụ đã commit. Chưa có hàng đợi bền vững/tự thử gửi lại; gửi sự kiện hiện đồng bộ sau commit. Không có giao diện ứng viên/admin/thông báo hoàn chỉnh chỉ vì API tương ứng đã được thêm.

## Bảo toàn dữ liệu và giới hạn

Không đổi file `.env` thật, dữ liệu uploads, revision migration, schema hay chạy seed/migration lên MySQL thật. Cách chạy backend/frontend giữ nguyên. Settings xử lý DEBUG=release của máy như false; seed vẫn đọc đúng `.env` của server. Health là liveness, không còn báo MySQL Connected khi chưa kiểm tra.

Kiểm thử gồm API cũ, các luồng mới và UI jsdom; SQLite không chứng minh khóa đồng thời/transaction hoặc migration trên MySQL thật. Chưa xác minh kết nối MySQL, SMTP thật, HTTPS, tải thực tế, giao diện trong trình duyệt thật và upload logo. Các phần này cần môi trường tích hợp; không thể kết luận toàn bộ NFR trong SRS chỉ từ cấu trúc thư mục và bộ test.


## Kết quả kiểm chứng cuối đợt

| Kiểm tra | Kết quả |
| --- | --- |
| Backend `python -m pytest tests -q` | 52 passed; 2 cảnh báo deprecation có sẵn |
| Frontend `npm test` | 21 passed |
| Bảng endpoint trong Word so với OpenAPI | 24/24 đúng method và đường dẫn; có test hồi quy đọc trực tiếp bản Word |
| Tham chiếu HTML nội bộ | 51 tham chiếu tồn tại |
| Cú pháp | Toàn bộ Python backend và JavaScript runtime hợp lệ |
| Bảo toàn frontend hiện có | 7 file CSS/API/UI giữ nội dung sau di chuyển, đối chiếu không kể CRLF/LF |
| Nguồn thiết kế | SHA-256 bản Word trong repo trùng file người dùng cung cấp |
| Git whitespace | `git diff --check` đạt |

Kiểm thử SMTP dùng transport giả lập; backend dùng SQLite. Kết quả này không thay thế kiểm tra MySQL, SMTP thật hoặc giao diện trong trình duyệt thật. Mã nguồn đã được commit và push lên `feat/architecture-api-alignment` tại `177d5f1`; chưa merge vào main. Kết quả test trên là lần chạy mã nguồn đã ghi nhận trước khi cập nhật tài liệu bàn giao, không phải một lần chạy mới chỉ để sửa báo cáo.
