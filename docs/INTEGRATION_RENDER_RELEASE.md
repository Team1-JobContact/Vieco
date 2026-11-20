# Tích hợp các nhánh cho bản triển khai Render

Ngày kiểm tra: 20/11/2026. Nhánh tích hợp: `integration/render-release`, nền `main` tại `6d5d9c5`.

## Phạm vi đã hợp nhất

| Nhánh | Thay đổi |
| --- | --- |
| `feat/ui-notifications-redesign` | Quản trị tài khoản/danh mục/nội dung, hồ sơ ứng viên, avatar, sửa vòng đời tin tuyển dụng và các lỗi giao diện |
| `feature/t05c352-e2e-recruitment` | Hosting dùng chung, TLS MySQL, readiness database, công cụ nhập snapshot và báo cáo E2E |
| `fix/render-api-cors` | Kết nối Static Site với API Render, cấu hình FRONTEND_URL và kiểm thử CORS |
| `feature/t05c34c-apply-api-tests` | Kiểm thử bổ sung API ứng tuyển |
| `feature/demo-companies-jobs-seed` | Hai lệnh seed demo cho 10 công ty và 43 tin tuyển dụng |
| `bugfix/company-brand-name` | Sửa tên thương hiệu và ký hiệu công ty khi chưa có logo |

Nhánh E2E đã bao gồm commit `01524ff` của `feature/t05c34b-integration-testing`, `feature/t05c34e-job-search-apply` và `feature/t05c34f-application-status-withdraw`; không cần merge lại các nhánh trỏ cùng commit. Các nhánh chức năng cũ còn lại đã có trong lịch sử tích hợp.

Không hợp nhất `feat/init-project`: đây là nhánh khởi tạo cũ với thay đổi xóa tài liệu và cấu trúc lồng thư mục, không phù hợp với cấu trúc đang sử dụng. Không xóa nhánh này hoặc các nhánh nguồn.

## Giải quyết xung đột

- Giữ API quản trị/hồ sơ và phần hosting chung trong cùng ứng dụng.
- Static Site `https://vieco-frontend.onrender.com` gọi `https://vieco.onrender.com/api/v1`. Chế độ shared vẫn dùng cùng origin; cấu hình API tường minh giữ quyền ưu tiên.
- CORS luôn cho phép FRONTEND_URL và các origin bổ sung trong CORS_ORIGINS; mặc định CORS_ORIGINS là `[]`. Cấu hình phát triển ở cổng 5500 hỗ trợ cả localhost và 127.0.0.1. Xác thực tiếp tục dùng Bearer token.
- Giữ kiểm tra SECRET_KEY tối thiểu 32 ký tự, đường dẫn uploads tính từ server, kết nối MySQL/TLS và ngày nghiệp vụ UTC+7.
- Giữ thông báo dễ đọc khi shared server thiếu SECRET_KEY hợp lệ.

## Kiểm chứng trong phiên tích hợp

| Kiểm tra | Kết quả |
| --- | --- |
| Toàn bộ backend sau khi giải quyết xung đột | 145 passed, không skip; 20 cảnh báo deprecation có sẵn |
| Seed demo bổ sung | 1 passed; 10 công ty PENDING, duyệt qua nghiệp vụ, 43 tin APPROVED; chạy lại không tăng số bản ghi |
| Toàn bộ frontend | 36 passed, không skip |
| Dependency Python | pip check đạt; đã cài Pillow theo requirements của nhánh hồ sơ/ảnh |
| Git | diff check đạt; không còn xung đột |

Backend và seed demo được kiểm tra bằng SQLite cô lập; SMTP bị tắt trong bài seed. Không chạy migration, seed hoặc nhập snapshot vào database thật. Không thay đổi `.env`, dữ liệu uploads, hai tệp nén cục bộ hoặc Environment trên Render. Chưa kiểm tra lại MySQL/Aiven, SMTP thật, Docker và dịch vụ Render với mã tích hợp.

## Sau khi Pull Request được duyệt

Repository yêu cầu ít nhất một lượt review chấp thuận trước khi merge vào main. Sau merge, triển khai commit mới cho cả hai dịch vụ Render theo [SETUP](SETUP.md#triển-khai-frontend-trên-render).

Backend cần SECRET_KEY riêng từ 32 ký tự, FRONTEND_URL đúng địa chỉ frontend, DATABASE_URL trỏ tới database online và CA/TLS phù hợp nếu dùng Aiven. Dùng `/api/v1/ready` để kiểm tra kết nối database; endpoint này chưa kiểm tra đủ bảng, seed hoặc toàn bộ nghiệp vụ. Các lệnh demo chỉ chạy khi người vận hành chủ động gọi.

Các PR #31, #32, #33 đã có nội dung trong nhánh tích hợp; giữ nguyên PR nguồn trong lúc chờ bản tích hợp được duyệt. Không cần triển khai từng nhánh riêng lên Render.
