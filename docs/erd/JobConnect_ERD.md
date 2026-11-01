# Tài liệu thiết kế hệ thống JobContact

## Danh sách module, mô tả module và thiết kế cơ sở dữ liệu

Phiên bản 1.0 | Ngày 01/11/2026 | Nhóm thực hiện: A, B, C, D | Căn cứ: SRS JobContact v1.0

## 1. Giới thiệu

### 1.1 Mục đích

Tài liệu mô tả cách chia hệ thống JobContact thành các module, trách nhiệm và quan hệ giữa các module, đồng thời thiết kế cơ sở dữ liệu (ERD và từ điển dữ liệu) đáp ứng các yêu cầu trong SRS. Công nghệ triển khai và kiến trúc chi tiết sẽ được chốt sau, tài liệu này giữ kiểu dữ liệu ở mức chung cho cơ sở dữ liệu quan hệ (PostgreSQL hoặc MySQL).

### 1.2 Quy ước thiết kế CSDL

- Tên bảng và cột dùng `snake_case`; tên bảng ở số nhiều.
- Mọi bảng có khóa chính `id` (BIGINT, tự tăng) và hai cột `created_at`, `updated_at` (TIMESTAMP). Ba cột này **không lặp lại** trong từ điển dữ liệu bên dưới.
- Khóa ngoại đặt tên `<bảng_số_ít>_id` (ví dụ `user_id`, `company_id`); khi một bảng có hai khóa ngoại cùng bảng đích thì thêm tiền tố nghĩa (ví dụ `reviewed_by`).
- Các trường trạng thái lưu dạng VARCHAR kèm ràng buộc CHECK theo danh sách giá trị nêu trong mô tả.
- Dữ liệu danh mục và dữ liệu đã phát sinh giao dịch không xóa cứng, dùng cột `is_active` hoặc `status` để ẩn.
- Ký hiệu: **PK** khóa chính, **FK** khóa ngoại, **NN** not null, **UQ** duy nhất.

## 2. Danh sách module và quan hệ phụ thuộc

### 2.1 Danh sách module

| Mã | Module | Phụ trách | Số bảng | Yêu cầu SRS |
| --- | --- | --- | --- | --- |
| M0 | Danh mục và cấu hình | A | 5 | FR-M0-01 đến FR-M0-06 |
| M1 | Tài khoản và hồ sơ | B | 11 | FR-M1-01 đến FR-M1-17 |
| M2 | Tuyển dụng và ứng tuyển | C | 5 | FR-M2-01 đến FR-M2-20 |
| M3 | Thông báo và thống kê (kèm phần mở rộng) | D | 6 | FR-M3-01 đến FR-M3-10 |

Tổng cộng 27 bảng. So với phân công ban đầu, M0 thêm bảng `static_pages` để đáp ứng FR-M0-05 (trang tĩnh).

### 2.2 Quan hệ phụ thuộc giữa các module

| Module | Phụ thuộc vào | Nội dung phụ thuộc |
| --- | --- | --- |
| M0 | Không | Là nền tảng dùng chung |
| M1 | M0 | Dùng tỉnh/thành, ngành nghề, kỹ năng cho hồ sơ ứng viên và công ty |
| M2 | M0, M1 | Dùng danh mục; tin gắn với công ty; đơn gắn với hồ sơ và CV của ứng viên |
| M3 | M1, M2 | Thông báo, nhắn tin, đánh giá, báo cáo tham chiếu người dùng, công ty, tin, đơn; thống kê đọc dữ liệu M1 và M2 |

Chiều phụ thuộc chỉ đi một hướng M0 → M1 → M2 → M3: module sau được tham chiếu khóa ngoại tới module trước, không làm ngược lại. Khi M1 hoặc M2 cần gửi thông báo, các module này gọi chức năng tạo thông báo của M3 qua một giao diện dịch vụ chung, không ghi trực tiếp vào bảng của M3.

## 3. Mô tả chi tiết module

### 3.1 Module M0: Danh mục và cấu hình

- **Trách nhiệm**: quản lý các danh mục dùng chung (ngành nghề, kỹ năng, tỉnh/thành), cấu hình hệ thống và trang tĩnh.
- **Actor**: Admin (quản lý); mọi actor (đọc danh mục).
- **Chức năng chính**: thêm, sửa, ẩn danh mục; cung cấp danh mục cho bộ lọc và biểu mẫu; sửa các tham số như thời hạn tin mặc định, dung lượng CV tối đa; soạn nội dung trang giới thiệu, điều khoản, FAQ.
- **Quy tắc**: BR-10, danh mục đang được dùng chỉ được ẩn, không xóa cứng.
- **Bảng**: `industries`, `skills`, `provinces`, `system_settings`, `static_pages`.

### 3.2 Module M1: Tài khoản và hồ sơ

- **Trách nhiệm**: xác thực, phân quyền, quản lý hồ sơ ứng viên, CV và hồ sơ công ty.
- **Actor**: Khách, Ứng viên, Nhà tuyển dụng, Admin.
- **Chức năng chính**: đăng ký hai loại tài khoản, xác thực email, đăng nhập/đăng xuất, quên và đổi mật khẩu, RBAC; hồ sơ ứng viên (thông tin chung, học vấn, kinh nghiệm, kỹ năng, CV, chế độ hiển thị); hồ sơ công ty và thành viên; Admin duyệt công ty, khóa/mở khóa tài khoản.
- **Quy tắc**: BR-01 (email duy nhất, phải xác thực), BR-02 (công ty được duyệt mới được đăng tin), BR-09 (tài khoản khóa không đăng nhập được); khóa tạm thời sau 5 lần đăng nhập sai (NFR-08).
- **Bảng**: `roles`, `users`, `email_verifications`, `password_resets`, `candidate_profiles`, `educations`, `work_experiences`, `candidate_skills`, `cvs`, `companies`, `company_members`.
- **Trạng thái công ty**: PENDING → APPROVED hoặc REJECTED (từ REJECTED có thể gửi duyệt lại về PENDING).

### 3.3 Module M2: Tuyển dụng và ứng tuyển

- **Trách nhiệm**: vòng đời tin tuyển dụng, tìm kiếm và lọc, ứng tuyển và xử lý đơn.
- **Actor**: Khách, Ứng viên, Nhà tuyển dụng, Admin.
- **Chức năng chính**: tạo, lưu nháp, sửa, đóng, mở lại, gia hạn tin; Admin duyệt hoặc gỡ tin; tìm kiếm theo từ khóa, lọc, sắp xếp, phân trang; ứng tuyển bằng CV và thư xin việc; lưu tin; theo dõi và rút đơn; nhà tuyển dụng xem ứng viên và đổi trạng thái đơn; tự động chuyển tin quá hạn sang HET\_HAN.
- **Quy tắc**: BR-03, BR-04, BR-05, BR-06, BR-07, BR-08.
- **Bảng**: `jobs`, `job_skills`, `applications`, `application_status_history`, `saved_jobs`.
- **Trạng thái tin** (`jobs.status`): DRAFT, PENDING, APPROVED, REJECTED, CLOSED, EXPIRED.
- **Trạng thái đơn** (`applications.status`): NEW, VIEWED, INTERVIEW, ACCEPTED, REJECTED, WITHDRAWN.

### 3.4 Module M3: Thông báo và thống kê

- **Trách nhiệm**: thông báo, thống kê và các chức năng mở rộng gắn với tương tác giữa người dùng.
- **Actor**: Ứng viên, Nhà tuyển dụng, Admin.
- **Chức năng cốt lõi**: thông báo trong hệ thống và email, đánh dấu đã đọc, dashboard nhà tuyển dụng và Admin.
- **Chức năng mở rộng**: nhắn tin (chỉ khi đã có đơn ứng tuyển), đánh giá công ty, báo cáo vi phạm và xử lý, nhật ký hoạt động.
- **Quy tắc**: BR-11. Dashboard không có bảng riêng, được tính bằng truy vấn tổng hợp trên `jobs`, `applications`, `users`; lượt xem tin dùng cột `view_count` của `jobs`.
- **Bảng**: `notifications`, `conversations`, `messages`, `company_reviews`, `reports`, `audit_logs`.

## 4. Từ điển dữ liệu

### 4.1 Module M0

**Bảng `industries`**: ngành nghề.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| name | VARCHAR(100) | NN, UQ | Tên ngành |
| slug | VARCHAR(120) | NN, UQ | Chuỗi dùng trong đường dẫn |
| is\_active | BOOLEAN | NN, mặc định true | Còn sử dụng hay đã ẩn |

**Bảng `skills`**: kỹ năng.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| name | VARCHAR(100) | NN, UQ | Tên kỹ năng |
| industry\_id | BIGINT | FK → industries, cho phép NULL | Ngành gợi ý của kỹ năng |
| is\_active | BOOLEAN | NN, mặc định true | Còn sử dụng hay đã ẩn |

**Bảng `provinces`**: tỉnh/thành phố.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| name | VARCHAR(100) | NN, UQ | Tên tỉnh/thành |
| code | VARCHAR(10) | NN, UQ | Mã tỉnh/thành |
| is\_active | BOOLEAN | NN, mặc định true | Còn sử dụng hay đã ẩn |

**Bảng `system_settings`**: cấu hình hệ thống dạng khóa-giá trị.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| setting\_key | VARCHAR(100) | NN, UQ | Khóa, ví dụ `job_default_days`, `cv_max_size_mb` |
| setting\_value | TEXT | NN | Giá trị |
| description | VARCHAR(255) |  | Giải thích |

**Bảng `static_pages`**: trang nội dung tĩnh.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| slug | VARCHAR(100) | NN, UQ | Ví dụ `gioi-thieu`, `dieu-khoan`, `faq` |
| title | VARCHAR(200) | NN | Tiêu đề |
| content | TEXT | NN | Nội dung |
| is\_published | BOOLEAN | NN, mặc định true | Có hiển thị công khai hay không |

### 4.2 Module M1

**Bảng `roles`**: vai trò.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| name | VARCHAR(30) | NN, UQ | ADMIN, CANDIDATE, EMPLOYER |
| description | VARCHAR(255) |  | Mô tả vai trò |

**Bảng `users`**: tài khoản.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| email | VARCHAR(255) | NN, UQ | Email đăng nhập |
| password\_hash | VARCHAR(255) | NN | Mật khẩu đã băm |
| role\_id | BIGINT | NN, FK → roles | Vai trò |
| full\_name | VARCHAR(150) | NN | Họ tên |
| phone | VARCHAR(20) |  | Số điện thoại |
| avatar\_url | VARCHAR(500) |  | Đường dẫn ảnh đại diện |
| is\_email\_verified | BOOLEAN | NN, mặc định false | Đã xác thực email |
| status | VARCHAR(20) | NN, mặc định ACTIVE | ACTIVE hoặc LOCKED |
| failed\_login\_count | INT | NN, mặc định 0 | Số lần đăng nhập sai liên tiếp |
| locked\_until | TIMESTAMP |  | Khóa tạm thời đến thời điểm này |
| last\_login\_at | TIMESTAMP |  | Lần đăng nhập gần nhất |

**Bảng `email_verifications`**: mã xác thực email.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| user\_id | BIGINT | NN, FK → users | Người dùng |
| token | VARCHAR(255) | NN, UQ | Mã xác thực |
| expires\_at | TIMESTAMP | NN | Hết hạn |
| used\_at | TIMESTAMP |  | Thời điểm đã dùng, NULL nếu chưa |

**Bảng `password_resets`**: mã đặt lại mật khẩu (cấu trúc giống `email_verifications`).

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| user\_id | BIGINT | NN, FK → users | Người dùng |
| token | VARCHAR(255) | NN, UQ | Mã đặt lại |
| expires\_at | TIMESTAMP | NN | Hết hạn |
| used\_at | TIMESTAMP |  | Thời điểm đã dùng |

**Bảng `candidate_profiles`**: hồ sơ ứng viên (quan hệ 1-1 với `users`).

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| user\_id | BIGINT | NN, UQ, FK → users | Chủ hồ sơ |
| date\_of\_birth | DATE |  | Ngày sinh |
| gender | VARCHAR(10) |  | MALE, FEMALE, OTHER |
| address | VARCHAR(255) |  | Địa chỉ |
| province\_id | BIGINT | FK → provinces | Tỉnh/thành |
| headline | VARCHAR(150) |  | Chức danh mong muốn |
| summary | TEXT |  | Giới thiệu bản thân |
| visibility | VARCHAR(10) | NN, mặc định PUBLIC | PUBLIC hoặc PRIVATE |

**Bảng `educations`**: học vấn.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| candidate\_profile\_id | BIGINT | NN, FK → candidate\_profiles | Hồ sơ |
| school\_name | VARCHAR(200) | NN | Trường |
| major | VARCHAR(150) |  | Chuyên ngành |
| degree | VARCHAR(50) |  | Bậc/bằng cấp |
| start\_date | DATE |  | Bắt đầu |
| end\_date | DATE |  | Kết thúc |
| description | TEXT |  | Ghi chú |

**Bảng `work_experiences`**: kinh nghiệm làm việc.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| candidate\_profile\_id | BIGINT | NN, FK → candidate\_profiles | Hồ sơ |
| company\_name | VARCHAR(200) | NN | Nơi làm việc |
| position | VARCHAR(150) | NN | Vị trí |
| start\_date | DATE | NN | Bắt đầu |
| end\_date | DATE |  | Kết thúc, NULL nếu đang làm |
| description | TEXT |  | Mô tả công việc |

**Bảng `candidate_skills`**: kỹ năng của ứng viên (bảng nối hồ sơ và kỹ năng).

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| candidate\_profile\_id | BIGINT | NN, FK → candidate\_profiles | Hồ sơ |
| skill\_id | BIGINT | NN, FK → skills | Kỹ năng |
| level | VARCHAR(20) |  | BEGINNER, INTERMEDIATE, ADVANCED |

Ràng buộc duy nhất: (`candidate_profile_id`, `skill_id`).

**Bảng `cvs`**: tệp CV.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| candidate\_profile\_id | BIGINT | NN, FK → candidate\_profiles | Chủ CV |
| file\_name | VARCHAR(255) | NN | Tên tệp gốc |
| file\_url | VARCHAR(500) | NN | Đường dẫn lưu trữ |
| file\_size | INT | NN | Dung lượng (byte) |
| is\_default | BOOLEAN | NN, mặc định false | CV mặc định |

Giới hạn tối đa 5 CV mỗi hồ sơ do ứng dụng kiểm soát.

**Bảng `companies`**: công ty.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| name | VARCHAR(200) | NN | Tên công ty |
| slug | VARCHAR(220) | NN, UQ | Dùng trong đường dẫn |
| logo\_url | VARCHAR(500) |  | Logo |
| description | TEXT |  | Giới thiệu |
| industry\_id | BIGINT | FK → industries | Ngành |
| size | VARCHAR(30) |  | Quy mô, ví dụ 1-50, 51-200 |
| website | VARCHAR(255) |  | Trang web |
| address | VARCHAR(255) |  | Địa chỉ |
| province\_id | BIGINT | FK → provinces | Tỉnh/thành |
| status | VARCHAR(20) | NN, mặc định PENDING | PENDING, APPROVED, REJECTED |
| reject\_reason | VARCHAR(500) |  | Lý do từ chối |
| reviewed\_by | BIGINT | FK → users | Admin duyệt |
| reviewed\_at | TIMESTAMP |  | Thời điểm duyệt |

**Bảng `company_members`**: thành viên công ty.

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| company\_id | BIGINT | NN, FK → companies | Công ty |
| user\_id | BIGINT | NN, UQ, FK → users | Nhà tuyển dụng (mỗi người thuộc một công ty) |
| member\_role | VARCHAR(20) | NN, mặc định MEMBER | OWNER hoặc MEMBER |
