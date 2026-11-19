# Kiểm tra trước khi đưa Vieco lên hosting — 18/11/2026

## Kết luận

Các luồng tuyển dụng chính chạy được trên trình duyệt thật với MySQL thật. Mã nguồn đã được sửa những lỗi phát hiện trong đợt kiểm tra này. Có thể chuẩn bị triển khai bản demo dùng chung sau khi xác nhận database Aiven và chuyển uploads lên máy chủ.

Chưa thể kết luận hoàn chỉnh 100% để vận hành dịch vụ công khai: chưa kiểm chứng Aiven/TLS bằng CA của nhóm, chưa thử SMTP thật, trang Liên hệ dùng mailto, và các liên kết chính sách chưa có trang nội dung riêng. Đây không phải chứng nhận đáp ứng toàn bộ SRS/NFR.

## Môi trường và cách giữ dữ liệu

- Mã nguồn được kiểm tra trên nhánh main, nền commit `6d5d9c5`, cộng các sửa đổi cục bộ chưa commit.
- Windows, Python 3.15.2, MySQL Community 8.0.45, Google Chrome qua Playwright.
- Dịch vụ MySQL80 của máy đang dừng và không khởi động được bằng quyền của phiên làm việc. Một tiến trình MySQL thử riêng được dựng ở `127.0.0.1:13306`, với mật khẩu ngẫu nhiên, dữ liệu lưu trong thư mục tạm riêng.
- Database thử `job_contact_audit` nhập từ snapshot MySQL 8.4 của nhóm: 30 bảng, migration `0003`. Uploads được sao chép sang thư mục kiểm thử. Tài khoản và các thao tác ghi thử chỉ nằm trong bản sao này.
- Database thứ hai `job_contact_schema_audit` dùng để kiểm tra migration từ đầu. Database phát triển `job_contact_db`, `.env` và uploads gốc giữ nguyên.
- Website/API thử đang chạy tại `http://127.0.0.1:8000`, đọc `.env.audit`. Đây là bản sao có thêm dữ liệu kiểm thử. Hosting dùng cấu hình `.env.shared` và dữ liệu thật của nhóm.

## Kết quả kiểm chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Backend pytest | **103 passed**, không skip; có 21 cảnh báo deprecation |
| Frontend Node/jsdom | **24 passed**, không skip |
| Bản snapshot trên MySQL thật | Nhập đủ 30 bảng; `alembic upgrade head` thành công; `alembic check` không có thay đổi schema |
| Database MySQL trống | Chạy `0001 → 0002 → 0003` thành công; `alembic check` không có thay đổi schema |
| HTTP với MySQL thật | **49 kiểm tra đạt**, gồm quyền truy cập, dữ liệu không hợp lệ, CV, logo, đơn ứng tuyển, đăng xuất |
| Đăng ký đồng thời cùng email | Một request 201, một request 409; không tạo trùng |
| Nộp đồng thời cùng một đơn | Một request 201, một request 409; không tạo trùng |
| Đọc đồng thời mức nhỏ | 20 request, 4 worker, tất cả HTTP 200; median 71,9 ms, max 94,5 ms trên máy thử. Không phải kết quả năng lực tải production |
| Tham chiếu file HTML | 17 file HTML, 192 tham chiếu cục bộ, không thiếu file |
| Trình duyệt công khai | 11 URL × 2 kích thước 1440/390 px; không lỗi JavaScript, lỗi máy chủ, ảnh hỏng hoặc tràn ngang |
| Trình duyệt có đăng nhập | 8 URL/tab × 2 kích thước; không lỗi JavaScript/lỗi máy chủ hoặc tràn ngang |
| CORS trên server đang chạy | Origin localhost:5500 được phép; origin không cấu hình bị từ chối |
| Dữ liệu riêng trong Git | `.env.audit`, `.env.shared`, `certs/ca.pem`, uploads được ignore; chỉ `.env.example` và uploads/.gitkeep được theo dõi |
| Docker/Linux/hosting | Chưa build/chạy Docker; chưa triển khai hoặc kiểm chứng máy chủ Linux/Render |

Bộ pytest dùng SQLite cô lập; các kiểm tra HTTP, trình duyệt và migration ở trên bổ sung bằng MySQL thật.

## Luồng người dùng đã chạy

Đã thử tạo/duyệt công ty, sau đó chạy các bước trên trình duyệt với HTTP thật:

1. Đăng ký ứng viên; đăng nhập bằng Admin, nhà tuyển dụng và ứng viên.
2. Nhà tuyển dụng điền biểu mẫu, lưu tin DRAFT vào MySQL, gửi duyệt PENDING.
3. Admin duyệt tin; tin xuất hiện qua API/trang công khai.
4. Ứng viên mở chi tiết, tải CV và nộp đơn qua hộp thoại ứng tuyển.
5. Tải lại trang vẫn hiển thị đã ứng tuyển, nút nộp lại bị khóa.
6. Nhà tuyển dụng xem hồ sơ, tải CV qua nút trên giao diện; nội dung tải xuống khớp file đã tải lên.
7. Nhà tuyển dụng mời phỏng vấn; ứng viên tải lại trang thấy trạng thái mới.
8. Ứng viên mở thông báo và đánh dấu tất cả đã đọc.

HTTP còn xác nhận: người khác không đọc được đơn/CV; sai vai trò bị chặn; file giả đuôi/SVG/quá dung lượng bị chặn; CV đã dùng được xóa mềm mà nhà tuyển dụng vẫn tải được; đóng/mở lại tin đúng vòng đời; token đã đăng xuất không dùng lại được.

## Các sửa lỗi trong đợt kiểm tra

| Vấn đề | Thay đổi và xác minh |
| --- | --- |
| Hạn tin/ngày sinh lấy ngày theo timezone máy chủ, khác ngày Việt Nam khi hosting chạy UTC | Dùng một hàm ngày nghiệp vụ UTC+7 cho schema, gửi/mở lại tin và lọc công khai; có test ranh giới 18:30 UTC = ngày hôm sau ở Việt Nam |
| Trang Liên hệ tràn ngang trên điện thoại | Thay grid inline bằng class để quy tắc responsive áp dụng; kiểm tra lại Chrome 390 px không tràn |
| Phục vụ cả thư mục client làm lộ log và file phát triển | Chỉ phục vụ index.html, pages và src; xác nhận log, package.json và thư mục tests trả 404, website/API vẫn hoạt động |
| CORS chấp nhận mọi origin | Chuyển sang CORS_ORIGINS cấu hình rõ; kiểm tra preflight được phép/từ chối |
| Chế độ shared có thể khởi động bằng debug/secret mặc định | Từ chối DEBUG=true, SECRET_KEY mặc định/ngắn, DATABASE_URL mặc định và Aiven không bật TLS; có test khởi động lỗi đúng thông báo |

Phần chuẩn bị chạy chung còn có cấu hình TLS dùng chung cho API/Alembic, readiness thực sự truy vấn DB, frontend dùng cùng origin với backend, công cụ nhập snapshot chỉ vào database trống, Docker/Compose và tài liệu vận hành.

## Những việc còn thiếu hoặc cần chốt

| Mục | Ảnh hưởng / bước tiếp theo |
| --- | --- |
| Chưa có `certs/ca.pem` của Aiven | Chưa xác thực được TLS và chưa kiểm tra/nhập database cloud. Lấy CA từ người quản lý dịch vụ Aiven trước |
| Dữ liệu hiện có trên Aiven chưa xác nhận | Nếu database trống thì nhập snapshot; nếu đã có bảng, kiểm tra/sao lưu trước khi quyết định giữ hay thay thế. Công cụ nhập hiện tự từ chối database có bảng |
| Chưa chuyển uploads lên hosting | Cần ổ lưu trữ bền vững và chép cả company/cvs lên đó |
| SMTP chưa cấu hình/thử thật | Đăng ký và thông báo trong web hoạt động; quên mật khẩu trả 503 đúng theo cấu hình. Cần SMTP để nhận email xác thực/reset/thông báo |
| Form Liên hệ dùng mailto | Mở ứng dụng email của người dùng, chưa có API lưu hoặc tiếp nhận liên hệ |
| Liên kết Điều khoản/Chính sách/Quy chế đang tới FAQ | Cần nội dung/trang riêng do nhóm xác nhận trước khi mở dịch vụ chính thức |
| Thư viện CV | Hiện là các bố cục tham khảo, không phải trình tạo/chỉnh sửa CV trực tuyến |
| Đối chiếu SRS/framework và vận hành lâu dài | Các báo cáo cũ đã ghi nhận khác biệt công nghệ so với tài liệu thiết kế. Cần thống nhất tiêu chí nghiệm thu; backup, HTTPS, SMTP, tải thực tế cần nghiệm thu trên hosting |

Không có thay đổi schema/migration mới trong đợt sửa lỗi này.

## Tệp bằng chứng và bước triển khai

Bằng chứng cục bộ nằm tại `../outputs/hosting-audit/` tính từ gốc repo: `browser-public.json`, `browser-workflow.json`, `http-audit.json`, `concurrency.json`, ảnh chụp trang desktop/mobile và log thử nghiệm. Thư mục này nằm ngoài repo và không được đưa lên hosting.

Xem [hướng dẫn Render từng bước](HOSTING_RENDER.md) để đưa website/API lên cùng một địa chỉ và giữ database Aiven hiện có. Tài liệu không đồng nghĩa dịch vụ đã được tạo hoặc phát sinh chi phí.
