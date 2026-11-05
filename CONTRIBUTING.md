# Quy ước làm việc trong dự án

## 1. Quy ước đặt tên nhánh

Mỗi nhánh nên tuân theo cấu trúc sau:

`loai-nhanh/ma-task-mo-ngan-gon`

### Các prefix thường dùng

- `feature/`: Dành cho việc phát triển tính năng mới
  - Ví dụ: API, giao diện, logic nghiệp vụ
- `bugfix/`: Dành cho việc sửa lỗi
- `hotfix/`: Dành cho việc sửa lỗi khẩn cấp trên môi trường production hoặc nhánh chính
- `docs/`: Dành cho việc cập nhật tài liệu, README, hướng dẫn

### Ví dụ thực tế

- Tạo tính năng đăng nhập cho task PB-010:
  - `feature/pb-010-login-api`
- Làm giao diện đăng ký cho task PB-012:
  - `feature/pb-012-register-ui`
- Sửa lỗi validate cho task PB-010:
  - `bugfix/pb-010-fix-validation`

---

## 2. Quy ước commit

Áp dụng chuẩn Conventional Commits để lịch sử Git rõ ràng, dễ theo dõi và hỗ trợ tự động hóa trong tương lai.

### Cấu trúc

`type(scope): message`

Hoặc đơn giản:

`type: message`

### Các loại commit phổ biến

- `feat`: Thêm một tính năng mới
- `fix`: Sửa một lỗi
- `docs`: Cập nhật tài liệu
- `style`: Format code, chỉnh sửa kiểu dáng, không thay đổi logic
- `refactor`: Tái cấu trúc code mà không sửa lỗi hoặc thêm tính năng mới
- `chore`: Thay đổi cấu hình build, thêm thư viện, file cấu hình, v.v.

### Ví dụ thực tế

- `feat(auth): add login api and password hashing`
- `fix(ui): resolve responsive issue on mobile login form`
- `docs: update readme with setup instructions`
- `chore: initialize project folder structure`

---

## 3. Lưu ý

- Nên đặt tên branch và commit ngắn gọn, rõ nghĩa.
- Tránh đặt tên mơ hồ như `fix-1`, `update`, `test`.
- Mỗi commit nên mô tả rõ mục đích thay đổi để dễ review và theo dõi.
