1. Quy ước đặt tên nhánh (Branch Naming Convention)
Cấu trúc chuẩn chung: loai-nhanh/ma-task-mo-ngan-gon

Các loại nhánh (Prefix):

feature/: Dành cho việc phát triển tính năng mới (Ví dụ các task liên quan đến API, giao diện...).

bugfix/: Dành cho việc sửa lỗi (Fix bug).

hotfix/: Dành cho việc sửa lỗi gấp trực tiếp trên production/nhánh chính.

docs/: Dành cho việc cập nhật tài liệu, README.

Ví dụ thực tế cho nhóm bạn:

Nhánh làm tính năng đăng nhập (Task PB-010): feature/pb-010-login-api

Nhánh làm giao diện đăng ký (Task PB-012): feature/pb-012-register-ui

Nhánh sửa lỗi validate: bugfix/pb-010-fix-validation

2. Quy ước Commit (Commit Convention)
Áp dụng chuẩn Conventional Commits để lịch sử git rõ ràng và dễ đọc, đồng thời hỗ trợ việc tự động hóa sau này:

Cấu trúc: type(scope): message (hoặc đơn giản là type: message)

Các loại Type phổ biến:

feat: Thêm một tính năng mới (feature).

fix: Sửa một lỗi (bug fix).

docs: Cập nhật tài liệu (README, tài liệu API,...).

style: Format code, thêm dấu chấm phẩy, không làm thay đổi logic code.

refactor: Tái cấu trúc code (không sửa lỗi, không thêm tính năng).

chore: Thay đổi cấu hình build, thêm thư viện, file cấu hình (ví dụ: .env.example).

Ví dụ thực tế:

feat(auth): add login api and password hashing

fix(ui): resolve responsive issue on mobile login form

docs: update readme with setup instructions

chore: initialize project folder structure
