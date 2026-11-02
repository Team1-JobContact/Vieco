# Software Requirements Specification (SRS)

Tài liệu đặc tả yêu cầu phần mềm của dự án JobConnect.

# Tài liệu đặc tả yêu cầu phần mềm (SRS)

## Nền tảng kết nối việc làm JobContact

Phiên bản 1.0 | Ngày 01/11/2026 | Nhóm thực hiện: Nhóm 1

## 1. Giới thiệu

### 1.1 Mục đích

Tài liệu này mô tả đầy đủ các yêu cầu của hệ thống JobContact, làm cơ sở thống nhất giữa các thành viên nhóm cho giai đoạn thiết kế, lập trình và kiểm thử. Đối tượng đọc gồm nhóm phát triển, giảng viên hướng dẫn và các bên liên quan.

### 1.2 Phạm vi

JobContact là website kết nối **ứng viên** với **nhà tuyển dụng**. Hệ thống cho phép:

- Nhà tuyển dụng đăng tin, nhận và quản lý hồ sơ ứng tuyển.
- Ứng viên tạo hồ sơ, tìm kiếm việc làm và ứng tuyển trực tuyến.
- Quản trị viên kiểm duyệt nội dung, quản lý người dùng và danh mục.

Ngoài phạm vi phiên bản này: ứng dụng di động riêng, thanh toán trực tuyến, phỏng vấn video, gợi ý việc làm bằng AI.

### 1.3 Định nghĩa, từ viết tắt

| **Thuật ngữ**               | **Giải thích**                                               |
| --------------------------- | ------------------------------------------------------------ |
| SRS                         | Software Requirements Specification, đặc tả yêu cầu phần mềm |
| Khách                       | Người truy cập chưa đăng nhập                                |
| Ứng viên (Job Seeker)       | Người dùng tìm việc                                          |
| Nhà tuyển dụng (Employer)   | Đại diện công ty đăng tin tuyển dụng                         |
| Admin                       | Quản trị viên hệ thống                                       |
| Tin tuyển dụng (Job)        | Bài đăng tuyển dụng của nhà tuyển dụng                       |
| Đơn ứng tuyển (Application) | Hồ sơ ứng viên nộp cho một tin tuyển dụng                    |
| CV                          | Hồ sơ xin việc dạng tệp do ứng viên tải lên                  |
| FR                          | Functional Requirement, yêu cầu chức năng                    |
| NFR                         | Non-functional Requirement, yêu cầu phi chức năng            |
| RBAC                        | Phân quyền theo vai trò                                      |
| MVP                         | Phiên bản tối thiểu có thể sử dụng                           |

### 1.4 Tài liệu tham khảo

- IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications.
- Các website tuyển dụng tham khảo về nghiệp vụ: TopCV, VietnamWorks, ITviec.

### 1.5 Bố cục tài liệu

Mục 2 mô tả tổng quan. Mục 3 liệt kê yêu cầu chức năng theo module M0-M3. Mục 4 nêu giao diện ngoài. Mục 5 nêu yêu cầu phi chức năng. Mục 6 nêu quy tắc nghiệp vụ. Mục 7 là phụ lục.

## 2. Mô tả tổng quan

### 2.1 Bối cảnh sản phẩm

JobContact là hệ thống web độc lập, gồm giao diện người dùng (frontend), máy chủ ứng dụng (backend), cơ sở dữ liệu quan hệ, kho lưu trữ tệp (CV, logo) và dịch vụ gửi email. Công nghệ cụ thể sẽ được chốt ở tài liệu thiết kế hệ thống.

### 2.2 Các nhóm chức năng chính

| **Mã** | **Module**              | **Nội dung**                                                                         |
| ------ | ----------------------- | ------------------------------------------------------------------------------------ |
| M0     | Danh mục và cấu hình    | Ngành nghề, kỹ năng, tỉnh/thành, cấu hình hệ thống, trang tĩnh                       |
| M1     | Tài khoản và hồ sơ      | Đăng ký, đăng nhập, phân quyền, hồ sơ ứng viên, CV, hồ sơ công ty                    |
| M2     | Tuyển dụng và ứng tuyển | Tin tuyển dụng, tìm kiếm, ứng tuyển, quản lý ứng viên                                |
| M3     | Thông báo và thống kê   | Thông báo, dashboard; mở rộng: nhắn tin, đánh giá, báo cáo vi phạm, nhật ký hệ thống |

### 2.3 Đặc điểm người dùng

| **Actor**      | **Mô tả**                                             | **Quyền chính**                                                  |
| -------------- | ----------------------------------------------------- | ---------------------------------------------------------------- |
| Khách          | Chưa đăng nhập                                        | Xem và tìm kiếm tin, xem hồ sơ công ty, đăng ký, đăng nhập       |
| Ứng viên       | Đã đăng ký vai trò ứng viên                           | Quản lý hồ sơ và CV, ứng tuyển, lưu việc, theo dõi đơn           |
| Nhà tuyển dụng | Đã đăng ký vai trò nhà tuyển dụng, công ty được duyệt | Quản lý hồ sơ công ty, đăng tin, xử lý đơn ứng tuyển             |
| Admin          | Quản trị hệ thống                                     | Duyệt công ty và tin, quản lý người dùng, danh mục, xem thống kê |

### 2.4 Môi trường vận hành

- Chạy trên trình duyệt hiện đại: Chrome, Firefox, Edge, Safari (hai phiên bản mới nhất).
- Hiển thị tốt trên máy tính, máy tính bảng và điện thoại (responsive).
- Máy chủ chạy trên Linux hoặc dịch vụ đám mây.

### 2.5 Ràng buộc

- Giao diện và nội dung bằng tiếng Việt.
- Mật khẩu phải được mã hóa một chiều, không lưu dạng thô.
- Tệp CV chỉ chấp nhận PDF, DOC, DOCX, tối đa 5 MB.
- Tuân thủ quy ước đặt tên CSDL đã thống nhất: snake_case, bảng số nhiều, khóa chính id, có created_at và updated_at.
- Thời gian thực hiện giới hạn trong khuôn khổ môn học/dự án.

### 2.6 Giả định và phụ thuộc

- Người dùng có kết nối Internet và địa chỉ email hợp lệ.
- Dịch vụ email (SMTP hoặc dịch vụ bên thứ ba) hoạt động ổn định.
- Mỗi tài khoản chỉ thuộc một vai trò: Ứng viên hoặc Nhà tuyển dụng (Admin được tạo sẵn).
- Một công ty có thể có nhiều thành viên nhà tuyển dụng.


### 2.7 Phạm vi phiên bản MVP

Phiên bản MVP tập trung hoàn thiện luồng tuyển dụng cơ bản để ứng viên và nhà tuyển dụng có thể sử dụng được.

**Chức năng thuộc MVP:**
- Đăng ký, xác thực email, đăng nhập, đăng xuất và đặt lại mật khẩu.
- Quản lý hồ sơ ứng viên và CV.
- Quản lý hồ sơ công ty và quy trình Admin duyệt công ty.
- Nhà tuyển dụng tạo, chỉnh sửa, đóng tin tuyển dụng.
- Admin duyệt hoặc từ chối tin tuyển dụng.
- Khách và ứng viên xem, tìm kiếm, lọc và xem chi tiết tin tuyển dụng.
- Ứng viên nộp đơn, theo dõi và rút đơn theo quy định.
- Nhà tuyển dụng xem hồ sơ ứng viên và cập nhật trạng thái đơn.
- Thông báo trong hệ thống cho các sự kiện chính.
- Admin quản lý tài khoản và danh mục cần thiết.

**Chức năng ngoài MVP, chỉ thực hiện khi còn thời gian:**
- Nhắn tin giữa ứng viên và nhà tuyển dụng.
- Đánh giá công ty.
- Báo cáo vi phạm và xử lý báo cáo.
- Nhật ký hoạt động dành cho Admin.
- Dashboard thống kê nâng cao.
- Đăng nhập bằng Google.

Các chức năng được đánh dấu ưu tiên Thấp trong bảng FR được xem là chức năng mở rộng, trừ khi nhóm và giảng viên thống nhất khác.

## 3. Yêu cầu chức năng

Quy ước: mã yêu cầu dạng **FR-Mx-yy**. Mức ưu tiên: **Cao** (bắt buộc MVP), **TB** (nên có), **Thấp** (mở rộng).

### 3.1 Module M0: Danh mục và cấu hình (phụ trách: A)

| **Mã**   | **Yêu cầu**                                                                  | **Actor** | **Ưu tiên** |
| -------- | ---------------------------------------------------------------------------- | --------- | ----------- |
| FR-M0-01 | Quản lý ngành nghề: thêm, sửa, ẩn/xóa, xem danh sách                         | Admin     | Cao         |
| FR-M0-02 | Quản lý danh mục kỹ năng: thêm, sửa, ẩn/xóa, tìm kiếm                        | Admin     | Cao         |
| FR-M0-03 | Quản lý danh mục tỉnh/thành phố                                              | Admin     | Cao         |
| FR-M0-04 | Cấu hình hệ thống: thời hạn tin mặc định, dung lượng CV tối đa, email gửi đi | Admin     | TB          |
| FR-M0-05 | Quản lý trang tĩnh: giới thiệu, điều khoản sử dụng, câu hỏi thường gặp       | Admin     | Thấp        |
| FR-M0-06 | Hiển thị danh mục ngành nghề, kỹ năng, tỉnh/thành cho các biểu mẫu và bộ lọc | Tất cả    | Cao         |

### 3.2 Module M1: Tài khoản và hồ sơ (phụ trách: B)

| **Mã**   | **Yêu cầu**                                                                                         | **Actor**         | **Ưu tiên** |
| -------- | --------------------------------------------------------------------------------------------------- | ----------------- | ----------- |
| FR-M1-01 | Đăng ký tài khoản ứng viên bằng email và mật khẩu                                                   | Khách             | Cao         |
| FR-M1-02 | Đăng ký tài khoản nhà tuyển dụng kèm thông tin công ty ban đầu                                      | Khách             | Cao         |
| FR-M1-03 | Xác thực email qua liên kết gửi về hộp thư                                                          | Khách             | Cao         |
| FR-M1-04 | Đăng nhập bằng email và mật khẩu                                                                    | Tất cả            | Cao         |
| FR-M1-05 | Đăng xuất                                                                                           | Người dùng        | Cao         |
| FR-M1-06 | Quên mật khẩu: gửi liên kết đặt lại có thời hạn                                                     | Người dùng        | Cao         |
| FR-M1-07 | Đổi mật khẩu khi đã đăng nhập                                                                       | Người dùng        | TB          |
| FR-M1-08 | Phân quyền theo vai trò (RBAC): chặn truy cập chức năng không thuộc vai trò                         | Hệ thống          | Cao         |
| FR-M1-09 | Quản lý hồ sơ cá nhân ứng viên: họ tên, ảnh, số điện thoại, ngày sinh, địa chỉ, giới thiệu bản thân | Ứng viên          | Cao         |
| FR-M1-10 | Quản lý học vấn, kinh nghiệm làm việc, kỹ năng (chọn từ danh mục M0)                                | Ứng viên          | Cao         |
| FR-M1-11 | Tải lên, xem, đặt CV mặc định, xóa CV (tối đa 5 CV)                                                 | Ứng viên          | Cao         |
| FR-M1-12 | Đặt chế độ hiển thị hồ sơ: công khai hoặc riêng tư                                                  | Ứng viên          | TB          |
| FR-M1-13 | Tạo và cập nhật hồ sơ công ty: tên, logo, mô tả, quy mô, ngành, địa chỉ, website                    | Nhà tuyển dụng    | Cao         |
| FR-M1-14 | Xem trang công ty công khai cùng các tin đang tuyển                                                 | Khách, Người dùng | Cao         |
| FR-M1-15 | Mời hoặc thêm thành viên vào công ty                                                                | Nhà tuyển dụng    | Thấp        |
| FR-M1-16 | Duyệt hoặc từ chối hồ sơ công ty, ghi lý do từ chối                                                 | Admin             | Cao         |
| FR-M1-17 | Xem danh sách, tìm kiếm người dùng; khóa/mở khóa tài khoản                                          | Admin             | Cao         |

### 3.3 Module M2: Tuyển dụng và ứng tuyển (phụ trách: C)

| **Mã**   | **Yêu cầu**                                                                                                                                     | **Actor**         | **Ưu tiên** |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | ----------- |
| FR-M2-01 | Tạo tin tuyển dụng: tiêu đề, mô tả, yêu cầu, quyền lợi, ngành, kỹ năng, địa điểm, mức lương, kinh nghiệm, hình thức làm việc, số lượng, hạn nộp | Nhà tuyển dụng    | Cao         |
| FR-M2-02 | Lưu nháp tin tuyển dụng                                                                                                                         | Nhà tuyển dụng    | TB          |
| FR-M2-03 | Chỉnh sửa tin (tin đã duyệt khi sửa nội dung chính cần duyệt lại)                                                                               | Nhà tuyển dụng    | Cao         |
| FR-M2-04 | Đóng tin, mở lại tin                                                                                                                            | Nhà tuyển dụng    | Cao         |
| FR-M2-05 | Gia hạn tin sắp hết hạn                                                                                                                         | Nhà tuyển dụng    | TB          |
| FR-M2-06 | Duyệt hoặc từ chối tin tuyển dụng, ghi lý do                                                                                                    | Admin             | Cao         |
| FR-M2-07 | Gỡ tin vi phạm                                                                                                                                  | Admin             | Cao         |
| FR-M2-08 | Xem danh sách tin đang tuyển, có phân trang                                                                                                     | Khách, Người dùng | Cao         |
| FR-M2-09 | Tìm kiếm tin theo từ khóa (tiêu đề, công ty, kỹ năng)                                                                                           | Khách, Người dùng | Cao         |
| FR-M2-10 | Lọc theo ngành, địa điểm, mức lương, kinh nghiệm, hình thức làm việc                                                                            | Khách, Người dùng | Cao         |
| FR-M2-11 | Sắp xếp theo mới nhất, lương, hạn nộp                                                                                                           | Khách, Người dùng | TB          |
| FR-M2-12 | Xem chi tiết tin tuyển dụng (ghi nhận lượt xem)                                                                                                 | Khách, Người dùng | Cao         |
| FR-M2-13 | Ứng tuyển: chọn CV, viết thư xin việc; mỗi tin chỉ ứng tuyển một lần                                                                            | Ứng viên          | Cao         |
| FR-M2-14 | Lưu tin yêu thích, xem và bỏ lưu                                                                                                                | Ứng viên          | TB          |
| FR-M2-15 | Theo dõi danh sách đơn đã nộp và trạng thái từng đơn                                                                                            | Ứng viên          | Cao         |
| FR-M2-16 | Rút đơn ứng tuyển khi chưa ở trạng thái Nhận hoặc Từ chối                                                                                       | Ứng viên          | TB          |
| FR-M2-17 | Xem danh sách ứng viên theo từng tin, lọc theo trạng thái                                                                                       | Nhà tuyển dụng    | Cao         |
| FR-M2-18 | Xem hồ sơ và tải CV của ứng viên đã ứng tuyển                                                                                                   | Nhà tuyển dụng    | Cao         |
| FR-M2-19 | Đổi trạng thái đơn: Mới, Đã xem, Phỏng vấn, Nhận, Từ chối; lưu lịch sử đổi trạng thái                                                           | Nhà tuyển dụng    | Cao         |
| FR-M2-20 | Tự động chuyển tin sang Hết hạn khi quá hạn nộp                                                                                                 | Hệ thống          | TB          |

### 3.4 Module M3: Thông báo và thống kê (phụ trách: D)

| **Mã**   | **Yêu cầu**                                                                                                  | **Actor**                | **Ưu tiên** |
| -------- | ------------------------------------------------------------------------------------------------------------ | ------------------------ | ----------- |
| FR-M3-01 | Thông báo trong hệ thống: có đơn mới, đổi trạng thái đơn, tin được duyệt/từ chối, công ty được duyệt/từ chối | Người dùng               | Cao         |
| FR-M3-02 | Gửi email thông báo cho các sự kiện quan trọng (xác thực, đổi trạng thái đơn, kết quả duyệt)                 | Hệ thống                 | TB          |
| FR-M3-03 | Xem danh sách thông báo, đánh dấu đã đọc, hiển thị số thông báo chưa đọc                                     | Người dùng               | Cao         |
| FR-M3-04 | Dashboard nhà tuyển dụng: số tin, lượt xem, số đơn theo tin và theo trạng thái                               | Nhà tuyển dụng           | TB          |
| FR-M3-05 | Dashboard admin: số người dùng, số tin, số đơn, tăng trưởng theo thời gian                                   | Admin                    | TB          |
| FR-M3-06 | Nhắn tin giữa ứng viên và nhà tuyển dụng, chỉ khi đã có đơn ứng tuyển                                        | Ứng viên, Nhà tuyển dụng | Thấp        |
| FR-M3-07 | Đánh giá công ty (điểm và nhận xét) bởi ứng viên đã từng ứng tuyển                                           | Ứng viên                 | Thấp        |
| FR-M3-08 | Báo cáo tin hoặc tài khoản vi phạm                                                                           | Người dùng               | Thấp        |
| FR-M3-09 | Xử lý báo cáo vi phạm: xem, xác nhận, bác bỏ, áp dụng biện pháp                                              | Admin                    | Thấp        |
| FR-M3-10 | Ghi nhật ký hoạt động quan trọng (duyệt, khóa tài khoản, gỡ tin) và cho Admin xem                            | Admin                    | Thấp        |


### 3.5 Luồng nghiệp vụ và Use Case chính

Các Use Case dưới đây mô tả luồng nghiệp vụ chính ở mức đủ để thống nhất thiết kế, lập trình và kiểm thử. Những chức năng mở rộng được ghi rõ trong phạm vi tương ứng.

#### UC-01: Đăng ký và xác thực tài khoản

- **Actor chính:** Khách
- **Điều kiện trước:** Người dùng chưa có tài khoản với email đăng ký.
- **Luồng chính:**
  1. Khách chọn đăng ký ứng viên hoặc nhà tuyển dụng.
  2. Nhập email, mật khẩu và thông tin bắt buộc theo loại tài khoản.
  3. Hệ thống kiểm tra định dạng dữ liệu và email chưa được sử dụng.
  4. Hệ thống tạo tài khoản ở trạng thái chưa xác thực.
  5. Hệ thống gửi email chứa liên kết xác thực có thời hạn.
  6. Người dùng mở liên kết xác thực.
  7. Hệ thống xác thực tài khoản và thông báo kết quả.
- **Luồng ngoại lệ:**
  - Email đã tồn tại: hệ thống thông báo và không tạo tài khoản trùng.
  - Dữ liệu không hợp lệ: hiển thị lỗi tại trường tương ứng.
  - Liên kết hết hạn hoặc không hợp lệ: yêu cầu gửi lại liên kết xác thực.
- **Kết quả:** Tài khoản được xác thực và có thể đăng nhập.

#### UC-02: Đăng nhập

- **Actor chính:** Khách
- **Điều kiện trước:** Tài khoản đã được đăng ký.
- **Luồng chính:**
  1. Người dùng nhập email và mật khẩu.
  2. Hệ thống kiểm tra thông tin đăng nhập.
  3. Hệ thống kiểm tra trạng thái tài khoản và trạng thái xác thực email.
  4. Nếu hợp lệ, hệ thống tạo phiên đăng nhập/token và chuyển người dùng đến trang phù hợp với vai trò.
- **Luồng ngoại lệ:**
  - Email hoặc mật khẩu sai: hiển thị thông báo chung, không tiết lộ trường nào sai.
  - Tài khoản bị khóa: từ chối đăng nhập và thông báo trạng thái.
  - Tài khoản chưa xác thực email: yêu cầu xác thực trước khi sử dụng chức năng cần đăng nhập.
  - Sai mật khẩu quá số lần cho phép: khóa đăng nhập tạm thời theo NFR-08.
- **Kết quả:** Người dùng đăng nhập thành công hoặc nhận thông báo lỗi phù hợp.

#### UC-03: Tìm kiếm và xem việc làm

- **Actor chính:** Khách, Ứng viên
- **Điều kiện trước:** Không yêu cầu đăng nhập.
- **Luồng chính:**
  1. Người dùng mở danh sách việc làm.
  2. Nhập từ khóa hoặc chọn bộ lọc.
  3. Hệ thống tìm các tin đang được công khai, còn hạn và đã duyệt.
  4. Hệ thống hiển thị kết quả có phân trang và thông tin tóm tắt.
  5. Người dùng chọn một tin để xem chi tiết.
  6. Hệ thống hiển thị nội dung tin và ghi nhận lượt xem.
- **Luồng ngoại lệ:** Nếu không có kết quả, hệ thống hiển thị thông báo và cho phép thay đổi từ khóa/bộ lọc.
- **Kết quả:** Người dùng xem được danh sách và chi tiết các tin phù hợp.

#### UC-04: Tạo và gửi tin tuyển dụng

- **Actor chính:** Nhà tuyển dụng
- **Điều kiện trước:** Đã đăng nhập, email đã xác thực và công ty đã được Admin duyệt.
- **Luồng chính:**
  1. Nhà tuyển dụng chọn tạo tin tuyển dụng.
  2. Nhập các trường bắt buộc của tin.
  3. Chọn lưu nháp hoặc gửi duyệt.
  4. Hệ thống kiểm tra dữ liệu và quyền thao tác.
  5. Nếu gửi duyệt, hệ thống chuyển tin sang trạng thái Chờ duyệt.
  6. Admin xem nội dung tin và chọn duyệt hoặc từ chối, kèm lý do khi từ chối.
  7. Hệ thống cập nhật trạng thái và thông báo kết quả cho nhà tuyển dụng.
- **Luồng ngoại lệ:**
  - Công ty chưa được duyệt hoặc tài khoản không đủ quyền: không cho gửi tin.
  - Thiếu/sai dữ liệu: yêu cầu chỉnh sửa.
  - Tin bị từ chối: nhà tuyển dụng được xem lý do và chỉnh sửa để gửi lại.
- **Kết quả:** Tin được lưu nháp, chờ duyệt, được duyệt hoặc bị từ chối.

#### UC-05: Ứng tuyển việc làm

- **Actor chính:** Ứng viên
- **Điều kiện trước:** Đã đăng nhập, email đã xác thực và hồ sơ có CV phù hợp.
- **Luồng chính:**
  1. Ứng viên mở tin đang tuyển.
  2. Chọn Ứng tuyển.
  3. Chọn CV và nhập thư xin việc nếu muốn.
  4. Hệ thống kiểm tra tin còn mở, chưa quá hạn và ứng viên chưa ứng tuyển tin này.
  5. Hệ thống tạo đơn ứng tuyển ở trạng thái Mới.
  6. Hệ thống thông báo cho nhà tuyển dụng.
  7. Ứng viên xem đơn trong danh sách đơn đã nộp.
- **Luồng ngoại lệ:**
  - Chưa đăng nhập hoặc chưa xác thực email: yêu cầu đăng nhập/xác thực.
  - Tin đã đóng, hết hạn hoặc không được duyệt: từ chối ứng tuyển.
  - Đã có đơn ứng tuyển cho tin đó: không tạo đơn trùng.
  - Chưa có CV: yêu cầu tải CV lên trước khi tiếp tục.
- **Kết quả:** Đơn ứng tuyển được tạo hoặc hệ thống hiển thị lý do không thể ứng tuyển.

#### UC-06: Quản lý và xử lý đơn ứng tuyển

- **Actor chính:** Nhà tuyển dụng
- **Điều kiện trước:** Đã đăng nhập; đơn thuộc tin tuyển dụng của công ty mà người dùng có quyền quản lý.
- **Luồng chính:**
  1. Nhà tuyển dụng mở danh sách ứng viên của một tin.
  2. Lọc đơn theo trạng thái nếu cần.
  3. Chọn một đơn để xem hồ sơ và CV.
  4. Cập nhật trạng thái đơn sang Đã xem, Phỏng vấn, Nhận hoặc Từ chối.
  5. Hệ thống kiểm tra quyền và tính hợp lệ của chuyển trạng thái.
  6. Hệ thống lưu trạng thái mới, lịch sử thay đổi và gửi thông báo cho ứng viên.
- **Luồng ngoại lệ:**
  - Đơn không thuộc công ty: từ chối truy cập.
  - Trạng thái chuyển không hợp lệ: yêu cầu chọn trạng thái phù hợp.
- **Kết quả:** Đơn được cập nhật và lịch sử xử lý được lưu.

#### UC-07: Rút đơn ứng tuyển

- **Actor chính:** Ứng viên
- **Điều kiện trước:** Ứng viên đã đăng nhập và là chủ sở hữu đơn.
- **Luồng chính:**
  1. Ứng viên mở danh sách đơn đã nộp.
  2. Chọn đơn đủ điều kiện rút và xác nhận thao tác.
  3. Hệ thống cập nhật đơn sang trạng thái Đã rút.
  4. Hệ thống ghi nhận thời điểm rút và thông báo cho nhà tuyển dụng.
- **Luồng ngoại lệ:** Nếu đơn đã ở trạng thái Nhận hoặc Từ chối, hệ thống không cho rút.
- **Kết quả:** Đơn được rút và không thể tiếp tục xử lý như đơn đang hoạt động.

#### UC-08: Quản lý hồ sơ công ty và duyệt công ty

- **Actor chính:** Nhà tuyển dụng, Admin
- **Điều kiện trước:** Nhà tuyển dụng đã đăng nhập.
- **Luồng chính:**
  1. Nhà tuyển dụng nhập/cập nhật thông tin công ty và gửi duyệt.
  2. Hệ thống lưu hồ sơ công ty ở trạng thái Chờ duyệt.
  3. Admin xem thông tin và chọn duyệt hoặc từ chối.
  4. Nếu từ chối, Admin nhập lý do.
  5. Hệ thống lưu trạng thái và thông báo kết quả.
- **Luồng ngoại lệ:** Thiếu thông tin bắt buộc thì không cho gửi duyệt.
- **Kết quả:** Công ty được duyệt hoặc bị từ chối; chỉ công ty được duyệt mới được đăng tin.

#### UC-09: Quản lý tài khoản và danh mục

- **Actor chính:** Admin
- **Điều kiện trước:** Admin đã đăng nhập.
- **Luồng chính:**
  1. Admin mở trang quản trị.
  2. Tìm kiếm người dùng hoặc chọn danh mục cần quản lý.
  3. Thực hiện xem, cập nhật, khóa/mở khóa tài khoản hoặc thêm/sửa/ẩn danh mục.
  4. Hệ thống kiểm tra quyền và dữ liệu.
  5. Hệ thống lưu thay đổi và hiển thị kết quả.
- **Luồng ngoại lệ:** Dữ liệu không hợp lệ hoặc mục đang được sử dụng không thể xóa cứng thì hệ thống yêu cầu ẩn thay vì xóa.
- **Kết quả:** Dữ liệu được quản lý theo quyền Admin.

### 3.6 Quy định dữ liệu đầu vào và kiểm tra

Các kiểm tra dưới đây áp dụng cho biểu mẫu tương ứng. Hệ thống phải kiểm tra ở phía máy chủ; kiểm tra phía giao diện chỉ nhằm hỗ trợ người dùng.

| Nhóm dữ liệu | Quy định |
|---|---|
| Email | Bắt buộc, đúng định dạng email, không trùng trong hệ thống |
| Mật khẩu | Bắt buộc, tối thiểu 8 ký tự; không lưu mật khẩu dạng thô |
| Họ tên | Bắt buộc khi hoàn thiện hồ sơ ứng viên |
| CV | Chỉ nhận PDF, DOC, DOCX; tối đa 5 MB mỗi tệp; tối đa 5 CV/tài khoản |
| Tin tuyển dụng | Bắt buộc có tiêu đề, mô tả, yêu cầu, địa điểm, hình thức làm việc và hạn nộp |
| Mức lương | Có thể nhập khoảng lương; giá trị tối thiểu không được lớn hơn giá trị tối đa |
| Hạn nộp | Phải là ngày hiện tại hoặc ngày trong tương lai khi tạo/gửi tin |
| Đơn ứng tuyển | Mỗi ứng viên chỉ có một đơn cho mỗi tin; phải chọn CV hợp lệ |
| Logo/ảnh đại diện | Chỉ nhận định dạng ảnh phổ biến; giới hạn dung lượng do cấu hình hệ thống quy định |
| Nội dung văn bản | Giới hạn độ dài hợp lý; từ chối dữ liệu vượt giới hạn hoặc không đúng kiểu |

Nếu trường dữ liệu tùy chọn không được nhập, hệ thống lưu giá trị rỗng/null theo thiết kế dữ liệu, không tự tạo dữ liệu giả.

### 3.7 Quy định chuyển trạng thái

#### 3.7.1 Trạng thái tin tuyển dụng

| Trạng thái hiện tại | Trạng thái tiếp theo hợp lệ | Người thực hiện/điều kiện |
|---|---|---|
| Nháp | Chờ duyệt | Nhà tuyển dụng gửi duyệt |
| Chờ duyệt | Đã duyệt | Admin duyệt |
| Chờ duyệt | Bị từ chối | Admin từ chối, phải có lý do |
| Bị từ chối | Nháp hoặc Chờ duyệt | Nhà tuyển dụng chỉnh sửa và gửi lại |
| Đã duyệt | Đã đóng | Nhà tuyển dụng đóng tin |
| Đã duyệt | Hết hạn | Hệ thống khi quá hạn |
| Đã đóng | Chờ duyệt | Nhà tuyển dụng mở lại; tin cần kiểm tra/duyệt lại theo chính sách |
| Hết hạn | Chờ duyệt | Nhà tuyển dụng gia hạn; tin cần được kiểm tra trước khi công khai |

Tin chỉ được hiển thị công khai khi ở trạng thái Đã duyệt, chưa quá hạn và chưa bị gỡ bởi Admin.

#### 3.7.2 Trạng thái đơn ứng tuyển

| Trạng thái hiện tại | Trạng thái tiếp theo hợp lệ | Người thực hiện |
|---|---|---|
| Mới | Đã xem | Nhà tuyển dụng |
| Mới | Đã rút | Ứng viên |
| Đã xem | Phỏng vấn | Nhà tuyển dụng |
| Đã xem | Nhận | Nhà tuyển dụng |
| Đã xem | Từ chối | Nhà tuyển dụng |
| Đã xem | Đã rút | Ứng viên |
| Phỏng vấn | Nhận | Nhà tuyển dụng |
| Phỏng vấn | Từ chối | Nhà tuyển dụng |
| Phỏng vấn | Đã rút | Ứng viên |

Các trạng thái Nhận, Từ chối và Đã rút là trạng thái kết thúc. Hệ thống không cho phép chuyển đơn từ trạng thái kết thúc sang trạng thái khác trong MVP.


## 4. Yêu cầu giao diện ngoài

### 4.1 Giao diện người dùng

- Giao diện web responsive, bố cục nhất quán, có thanh điều hướng và ô tìm kiếm ở trang chủ.
- Thông báo lỗi và xác nhận rõ ràng bằng tiếng Việt, kiểm tra dữ liệu nhập ở cả phía client và server.
- Các trang chính: Trang chủ, Danh sách việc làm, Chi tiết việc làm, Trang công ty, Đăng ký/Đăng nhập, Hồ sơ ứng viên, Quản lý tin của nhà tuyển dụng, Quản lý ứng viên, Trang quản trị.

### 4.2 Giao diện phần mềm

- Dịch vụ email (SMTP hoặc nhà cung cấp bên thứ ba) để gửi xác thực và thông báo.
- Kho lưu trữ tệp (hệ thống tệp máy chủ hoặc lưu trữ đám mây) cho CV, logo, ảnh đại diện.
- Cơ sở dữ liệu quan hệ.
- Đăng nhập bằng Google: tùy chọn, thuộc phạm vi mở rộng.

### 4.3 Giao diện phần cứng

Không có yêu cầu phần cứng đặc thù ngoài thiết bị có trình duyệt web.


### 4.4 Quy tắc phản hồi và thông báo giao diện

- Mỗi thao tác tạo, cập nhật, xóa/ẩn, gửi duyệt hoặc thay đổi trạng thái phải hiển thị kết quả thành công hoặc thất bại.
- Khi dữ liệu không hợp lệ, hệ thống hiển thị thông báo tiếng Việt gần trường dữ liệu tương ứng.
- Khi thao tác bị từ chối do không đủ quyền, hệ thống thông báo không có quyền thực hiện và không tiết lộ dữ liệu bị hạn chế.
- Trước thao tác có ảnh hưởng đáng kể như rút đơn, đóng tin hoặc khóa tài khoản, hệ thống yêu cầu người dùng xác nhận.
- Danh sách có nhiều dữ liệu phải hỗ trợ phân trang; bộ lọc và từ khóa cần được giữ lại khi người dùng chuyển trang.

## 5. Yêu cầu phi chức năng

| **Mã** | **Nhóm**       | **Yêu cầu**                                                                              |
| ------ | -------------- | ---------------------------------------------------------------------------------------- |
| NFR-01 | Hiệu năng      | Trang thông thường tải trong tối đa 3 giây trên mạng ổn định                             |
| NFR-02 | Hiệu năng      | Tìm kiếm và lọc việc làm trả kết quả trong tối đa 2 giây với khoảng 10.000 tin           |
| NFR-03 | Hiệu năng      | Hỗ trợ tối thiểu 100 người dùng truy cập đồng thời                                       |
| NFR-04 | Bảo mật        | Mật khẩu được băm bằng thuật toán an toàn (ví dụ bcrypt), tối thiểu 8 ký tự              |
| NFR-05 | Bảo mật        | Toàn bộ truyền tải qua HTTPS; phiên đăng nhập dùng token (JWT) có thời hạn               |
| NFR-06 | Bảo mật        | Chống SQL Injection, XSS, CSRF; kiểm tra và làm sạch dữ liệu đầu vào                     |
| NFR-07 | Bảo mật        | Phân quyền chặt chẽ; CV chỉ được xem bởi chủ sở hữu và nhà tuyển dụng nhận đơn tương ứng |
| NFR-08 | Bảo mật        | Khóa tạm thời đăng nhập sau 5 lần sai liên tiếp                                          |
| NFR-09 | Khả dụng       | Giao diện dễ dùng, người dùng mới hoàn thành ứng tuyển trong tối đa 5 thao tác chính     |
| NFR-10 | Độ tin cậy     | Hệ thống hoạt động tối thiểu 99% thời gian; sao lưu cơ sở dữ liệu định kỳ hằng ngày      |
| NFR-11 | Tương thích    | Chạy đúng trên Chrome, Firefox, Edge, Safari; hiển thị tốt từ màn hình 360 px            |
| NFR-12 | Bảo trì        | Mã nguồn theo cấu trúc module, có chú thích; tài liệu đồng bộ với hệ thống               |
| NFR-13 | Mở rộng        | Cho phép thêm module mới và tăng tải mà không phải thiết kế lại CSDL                     |
| NFR-14 | Quyền riêng tư | Chỉ thu thập dữ liệu cá nhân cần thiết; hồ sơ riêng tư không xuất hiện công khai         |


### 5.1 Tiêu chí kiểm thử cho yêu cầu phi chức năng

Các tiêu chí NFR được kiểm thử trong môi trường triển khai thử nghiệm với cấu hình và dữ liệu được ghi nhận rõ ràng.

- **NFR-01:** Đo thời gian tải trang thông thường bằng dữ liệu mẫu; mục tiêu tối đa 3 giây trên mạng ổn định.
- **NFR-02:** Kiểm thử tìm kiếm/lọc với khoảng 10.000 tin tuyển dụng; thời gian phản hồi mục tiêu tối đa 2 giây.
- **NFR-03:** Thực hiện kiểm thử tải với tối thiểu 100 phiên truy cập đồng thời; ghi nhận thời gian phản hồi và lỗi.
- **NFR-04 đến NFR-08:** Kiểm thử xác thực, phân quyền, giới hạn đăng nhập, truy cập trái phép và các trường hợp dữ liệu đầu vào không an toàn.
- **NFR-09:** Thực hiện kiểm thử khả dụng bằng cách yêu cầu người dùng mới hoàn thành luồng ứng tuyển trong tối đa 5 thao tác chính, không tính thao tác đăng nhập/xác thực nếu đã hoàn tất trước đó.
- **NFR-10:** Sao lưu dữ liệu định kỳ; nhóm cần xác định cách kiểm tra khả năng khôi phục trong giai đoạn triển khai.
- **NFR-11:** Kiểm tra giao diện trên các trình duyệt và kích thước màn hình đã nêu.
- **NFR-12:** Kiểm tra cấu trúc module, quy ước mã nguồn và mức độ đồng bộ giữa tài liệu với chức năng thực tế.


## 6. Quy tắc nghiệp vụ

| **Mã** | **Quy tắc**                                                                                                |
| ------ | ---------------------------------------------------------------------------------------------------------- |
| BR-01  | Email là duy nhất trong hệ thống; tài khoản chưa xác thực email không được ứng tuyển hoặc đăng tin         |
| BR-02  | Nhà tuyển dụng chỉ được đăng tin khi công ty đã được Admin duyệt                                           |
| BR-03  | Tin tuyển dụng chỉ hiển thị công khai khi ở trạng thái Đã duyệt và chưa quá hạn                            |
| BR-04  | Vòng đời tin: Nháp, Chờ duyệt, Đã duyệt, Bị từ chối, Đã đóng, Hết hạn                                      |
| BR-05  | Mỗi ứng viên chỉ ứng tuyển một lần cho mỗi tin; chỉ ứng tuyển tin đang mở                                  |
| BR-06  | Vòng đời đơn: Mới, Đã xem, Phỏng vấn, Nhận hoặc Từ chối; ứng viên có thể rút đơn trước khi có kết quả cuối |
| BR-07  | Mỗi lần đổi trạng thái đơn phải được lưu lịch sử (thời điểm, người thực hiện)                              |
| BR-08  | Nhà tuyển dụng chỉ xem được đơn của các tin thuộc công ty mình                                             |
| BR-09  | Tài khoản bị khóa không thể đăng nhập; dữ liệu cũ vẫn được giữ lại                                         |
| BR-10  | Ngành nghề, kỹ năng, tỉnh/thành đang được sử dụng chỉ được ẩn, không xóa cứng                              |
| BR-11  | Chỉ ứng viên đã ứng tuyển công ty mới được đánh giá công ty đó (mở rộng)                                   |


### 6.1 Quy tắc nghiệp vụ bổ sung

| **Mã** | **Quy tắc** |
|---|---|
| BR-12 | Tài khoản nhà tuyển dụng chỉ được tạo hoặc gửi tin tuyển dụng khi công ty liên kết đã được Admin duyệt. |
| BR-13 | Một tin tuyển dụng phải thuộc một công ty; chỉ thành viên có quyền phù hợp của công ty đó mới được quản lý tin. |
| BR-14 | Tin tuyển dụng bị từ chối phải có lý do; nhà tuyển dụng có thể chỉnh sửa và gửi lại để duyệt. |
| BR-15 | Mỗi đơn ứng tuyển phải tham chiếu một ứng viên, một tin tuyển dụng và một CV được chọn tại thời điểm nộp đơn. |
| BR-16 | CV của ứng viên chỉ được tải bởi chính ứng viên hoặc nhà tuyển dụng có quyền xem đơn ứng tuyển tương ứng; Admin chỉ truy cập khi cần xử lý quản trị theo quyền được cấp. |
| BR-17 | Đơn ứng tuyển ở trạng thái Nhận, Từ chối hoặc Đã rút không được chuyển tiếp trong MVP. |
| BR-18 | Khi tin tuyển dụng đóng hoặc hết hạn, hệ thống không nhận đơn ứng tuyển mới; các đơn đã nộp vẫn được lưu và quản lý. |
| BR-19 | Khi tài khoản bị khóa, người dùng không thể đăng nhập hoặc thực hiện thao tác yêu cầu xác thực; dữ liệu liên quan không bị xóa. |
| BR-20 | Thao tác thay đổi trạng thái tin, đơn ứng tuyển, công ty hoặc tài khoản phải lưu thời điểm và người thực hiện khi phù hợp. |
| BR-21 | Dữ liệu danh mục đang được tham chiếu bởi tin/hồ sơ không được xóa cứng; Admin chỉ được ẩn hoặc ngừng sử dụng. |
| BR-22 | Ứng viên chỉ được rút đơn của chính mình và chỉ trước khi đơn ở trạng thái kết thúc. |


## 7. Phụ lục

### 7.1 Ma trận actor và module

| **Actor**      | **M0**         | **M1**                           | **M2**                            | **M3**                            |
| -------------- | -------------- | -------------------------------- | --------------------------------- | --------------------------------- |
| Khách          | Xem danh mục   | Đăng ký, đăng nhập, xem công ty  | Xem, tìm kiếm, lọc việc           | Không                             |
| Ứng viên       | Xem danh mục   | Hồ sơ, CV                        | Ứng tuyển, lưu việc, theo dõi đơn | Thông báo, nhắn tin, đánh giá     |
| Nhà tuyển dụng | Xem danh mục   | Hồ sơ công ty                    | Đăng tin, quản lý ứng viên        | Thông báo, dashboard, nhắn tin    |
| Admin          | Quản lý đầy đủ | Duyệt công ty, quản lý tài khoản | Duyệt, gỡ tin                     | Dashboard, xử lý báo cáo, nhật ký |

### 7.2 Thống kê yêu cầu chức năng

| **Module** | **Cao** | **TB** | **Thấp** | **Tổng** |
| ---------- | ------- | ------ | -------- | -------- |
| M0         | 4       | 1      | 1        | 6        |
| M1         | 13      | 2      | 2        | 17       |
| M2         | 14      | 6      | 0        | 20       |
| M3         | 2       | 3      | 5        | 10       |

### 7.3 Việc cần chốt ở bước tiếp theo

- Công nghệ (tech stack) và kiến trúc triển khai: ghi trong tài liệu thiết kế hệ thống.
- Các bảng CSDL, ERD và mô tả chi tiết từng module: ghi trong tài liệu thiết kế hệ thống.
