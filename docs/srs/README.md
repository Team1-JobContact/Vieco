# Software Requirements Specification (SRS)

Tài liệu đặc tả yêu cầu phần mềm của dự án JobConnect.

# Tài liệu đặc tả yêu cầu phần mềm (SRS)

## Nền tảng kết nối việc làm JobContact

Phiên bản 1.0 | Ngày 01/11/2026 | Nhóm thực hiện: A, B, C, D

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

| Thuật ngữ | Giải thích |
| --- | --- |
| SRS | Software Requirements Specification, đặc tả yêu cầu phần mềm |
| Khách | Người truy cập chưa đăng nhập |
| Ứng viên (Job Seeker) | Người dùng tìm việc |
| Nhà tuyển dụng (Employer) | Đại diện công ty đăng tin tuyển dụng |
| Admin | Quản trị viên hệ thống |
| Tin tuyển dụng (Job) | Bài đăng tuyển dụng của nhà tuyển dụng |
| Đơn ứng tuyển (Application) | Hồ sơ ứng viên nộp cho một tin tuyển dụng |
| CV | Hồ sơ xin việc dạng tệp do ứng viên tải lên |
| FR | Functional Requirement, yêu cầu chức năng |
| NFR | Non-functional Requirement, yêu cầu phi chức năng |
| RBAC | Phân quyền theo vai trò |
| MVP | Phiên bản tối thiểu có thể sử dụng |

### 1.4 Tài liệu tham khảo

- IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications.
- Các website tuyển dụng tham khảo về nghiệp vụ: TopCV, VietnamWorks, ITviec.

### 1.5 Bố cục tài liệu

Mục 2 mô tả tổng quan. Mục 3 liệt kê yêu cầu chức năng theo module M0-M3. Mục 4 nêu giao diện ngoài. Mục 5 nêu yêu cầu phi chức năng. Mục 6 nêu quy tắc nghiệp vụ. Mục 7 là phụ lục.

## 2. Mô tả tổng quan

### 2.1 Bối cảnh sản phẩm

JobContact là hệ thống web độc lập, gồm giao diện người dùng (frontend), máy chủ ứng dụng (backend), cơ sở dữ liệu quan hệ, kho lưu trữ tệp (CV, logo) và dịch vụ gửi email. Công nghệ cụ thể sẽ được chốt ở tài liệu thiết kế hệ thống.

### 2.2 Các nhóm chức năng chính

| Mã | Module | Nội dung |
| --- | --- | --- |
| M0 | Danh mục và cấu hình | Ngành nghề, kỹ năng, tỉnh/thành, cấu hình hệ thống, trang tĩnh |
| M1 | Tài khoản và hồ sơ | Đăng ký, đăng nhập, phân quyền, hồ sơ ứng viên, CV, hồ sơ công ty |
| M2 | Tuyển dụng và ứng tuyển | Tin tuyển dụng, tìm kiếm, ứng tuyển, quản lý ứng viên |
| M3 | Thông báo và thống kê | Thông báo, dashboard; mở rộng: nhắn tin, đánh giá, báo cáo vi phạm, nhật ký hệ thống |

### 2.3 Đặc điểm người dùng

| Actor | Mô tả | Quyền chính |
| --- | --- | --- |
| Khách | Chưa đăng nhập | Xem và tìm kiếm tin, xem hồ sơ công ty, đăng ký, đăng nhập |
| Ứng viên | Đã đăng ký vai trò ứng viên | Quản lý hồ sơ và CV, ứng tuyển, lưu việc, theo dõi đơn |
| Nhà tuyển dụng | Đã đăng ký vai trò nhà tuyển dụng, công ty được duyệt | Quản lý hồ sơ công ty, đăng tin, xử lý đơn ứng tuyển |
| Admin | Quản trị hệ thống | Duyệt công ty và tin, quản lý người dùng, danh mục, xem thống kê |

### 2.4 Môi trường vận hành

- Chạy trên trình duyệt hiện đại: Chrome, Firefox, Edge, Safari (hai phiên bản mới nhất).
- Hiển thị tốt trên máy tính, máy tính bảng và điện thoại (responsive).
- Máy chủ chạy trên Linux hoặc dịch vụ đám mây.

### 2.5 Ràng buộc

- Giao diện và nội dung bằng tiếng Việt.
- Mật khẩu phải được mã hóa một chiều, không lưu dạng thô.
- Tệp CV chỉ chấp nhận PDF, DOC, DOCX, tối đa 5 MB.
- Tuân thủ quy ước đặt tên CSDL đã thống nhất: snake\_case, bảng số nhiều, khóa chính id, có created\_at và updated\_at.
- Thời gian thực hiện giới hạn trong khuôn khổ môn học/dự án.

### 2.6 Giả định và phụ thuộc

- Người dùng có kết nối Internet và địa chỉ email hợp lệ.
- Dịch vụ email (SMTP hoặc dịch vụ bên thứ ba) hoạt động ổn định.
- Mỗi tài khoản chỉ thuộc một vai trò: Ứng viên hoặc Nhà tuyển dụng (Admin được tạo sẵn).
- Một công ty có thể có nhiều thành viên nhà tuyển dụng.

## 3. Yêu cầu chức năng

Quy ước: mã yêu cầu dạng **FR-Mx-yy**. Mức ưu tiên: **Cao** (bắt buộc MVP), **TB** (nên có), **Thấp** (mở rộng).

### 3.1 Module M0: Danh mục và cấu hình (phụ trách: A)

| Mã | Yêu cầu | Actor | Ưu tiên |
| --- | --- | --- | --- |
| FR-M0-01 | Quản lý ngành nghề: thêm, sửa, ẩn/xóa, xem danh sách | Admin | Cao |
| FR-M0-02 | Quản lý danh mục kỹ năng: thêm, sửa, ẩn/xóa, tìm kiếm | Admin | Cao |
| FR-M0-03 | Quản lý danh mục tỉnh/thành phố | Admin | Cao |
| FR-M0-04 | Cấu hình hệ thống: thời hạn tin mặc định, dung lượng CV tối đa, email gửi đi | Admin | TB |
| FR-M0-05 | Quản lý trang tĩnh: giới thiệu, điều khoản sử dụng, câu hỏi thường gặp | Admin | Thấp |
| FR-M0-06 | Hiển thị danh mục ngành nghề, kỹ năng, tỉnh/thành cho các biểu mẫu và bộ lọc | Tất cả | Cao |

### 3.2 Module M1: Tài khoản và hồ sơ (phụ trách: B)

| Mã | Yêu cầu | Actor | Ưu tiên |
| --- | --- | --- | --- |
| FR-M1-01 | Đăng ký tài khoản ứng viên bằng email và mật khẩu | Khách | Cao |
| FR-M1-02 | Đăng ký tài khoản nhà tuyển dụng kèm thông tin công ty ban đầu | Khách | Cao |
| FR-M1-03 | Xác thực email qua liên kết gửi về hộp thư | Khách | Cao |
| FR-M1-04 | Đăng nhập bằng email và mật khẩu | Tất cả | Cao |
| FR-M1-05 | Đăng xuất | Người dùng | Cao |
| FR-M1-06 | Quên mật khẩu: gửi liên kết đặt lại có thời hạn | Người dùng | Cao |
| FR-M1-07 | Đổi mật khẩu khi đã đăng nhập | Người dùng | TB |
| FR-M1-08 | Phân quyền theo vai trò (RBAC): chặn truy cập chức năng không thuộc vai trò | Hệ thống | Cao |
| FR-M1-09 | Quản lý hồ sơ cá nhân ứng viên: họ tên, ảnh, số điện thoại, ngày sinh, địa chỉ, giới thiệu bản thân | Ứng viên | Cao |
| FR-M1-10 | Quản lý học vấn, kinh nghiệm làm việc, kỹ năng (chọn từ danh mục M0) | Ứng viên | Cao |
| FR-M1-11 | Tải lên, xem, đặt CV mặc định, xóa CV (tối đa 5 CV) | Ứng viên | Cao |
| FR-M1-12 | Đặt chế độ hiển thị hồ sơ: công khai hoặc riêng tư | Ứng viên | TB |
| FR-M1-13 | Tạo và cập nhật hồ sơ công ty: tên, logo, mô tả, quy mô, ngành, địa chỉ, website | Nhà tuyển dụng | Cao |
| FR-M1-14 | Xem trang công ty công khai cùng các tin đang tuyển | Khách, Người dùng | Cao |
| FR-M1-15 | Mời hoặc thêm thành viên vào công ty | Nhà tuyển dụng | Thấp |
| FR-M1-16 | Duyệt hoặc từ chối hồ sơ công ty, ghi lý do từ chối | Admin | Cao |
| FR-M1-17 | Xem danh sách, tìm kiếm người dùng; khóa/mở khóa tài khoản | Admin | Cao |

### 3.3 Module M2: Tuyển dụng và ứng tuyển (phụ trách: C)

| Mã | Yêu cầu | Actor | Ưu tiên |
| --- | --- | --- | --- |
| FR-M2-01 | Tạo tin tuyển dụng: tiêu đề, mô tả, yêu cầu, quyền lợi, ngành, kỹ năng, địa điểm, mức lương, kinh nghiệm, hình thức làm việc, số lượng, hạn nộp | Nhà tuyển dụng | Cao |
| FR-M2-02 | Lưu nháp tin tuyển dụng | Nhà tuyển dụng | TB |
| FR-M2-03 | Chỉnh sửa tin (tin đã duyệt khi sửa nội dung chính cần duyệt lại) | Nhà tuyển dụng | Cao |
| FR-M2-04 | Đóng tin, mở lại tin | Nhà tuyển dụng | Cao |
| FR-M2-05 | Gia hạn tin sắp hết hạn | Nhà tuyển dụng | TB |
| FR-M2-06 | Duyệt hoặc từ chối tin tuyển dụng, ghi lý do | Admin | Cao |
| FR-M2-07 | Gỡ tin vi phạm | Admin | Cao |
| FR-M2-08 | Xem danh sách tin đang tuyển, có phân trang | Khách, Người dùng | Cao |
| FR-M2-09 | Tìm kiếm tin theo từ khóa (tiêu đề, công ty, kỹ năng) | Khách, Người dùng | Cao |
| FR-M2-10 | Lọc theo ngành, địa điểm, mức lương, kinh nghiệm, hình thức làm việc | Khách, Người dùng | Cao |
| FR-M2-11 | Sắp xếp theo mới nhất, lương, hạn nộp | Khách, Người dùng | TB |
| FR-M2-12 | Xem chi tiết tin tuyển dụng (ghi nhận lượt xem) | Khách, Người dùng | Cao |
| FR-M2-13 | Ứng tuyển: chọn CV, viết thư xin việc; mỗi tin chỉ ứng tuyển một lần | Ứng viên | Cao |
| FR-M2-14 | Lưu tin yêu thích, xem và bỏ lưu | Ứng viên | TB |
| FR-M2-15 | Theo dõi danh sách đơn đã nộp và trạng thái từng đơn | Ứng viên | Cao |
| FR-M2-16 | Rút đơn ứng tuyển khi chưa ở trạng thái Nhận hoặc Từ chối | Ứng viên | TB |
| FR-M2-17 | Xem danh sách ứng viên theo từng tin, lọc theo trạng thái | Nhà tuyển dụng | Cao |
| FR-M2-18 | Xem hồ sơ và tải CV của ứng viên đã ứng tuyển | Nhà tuyển dụng | Cao |
| FR-M2-19 | Đổi trạng thái đơn: Mới, Đã xem, Phỏng vấn, Nhận, Từ chối; lưu lịch sử đổi trạng thái | Nhà tuyển dụng | Cao |
| FR-M2-20 | Tự động chuyển tin sang Hết hạn khi quá hạn nộp | Hệ thống | TB |

### 3.4 Module M3: Thông báo và thống kê (phụ trách: D)

| Mã | Yêu cầu | Actor | Ưu tiên |
| --- | --- | --- | --- |
| FR-M3-01 | Thông báo trong hệ thống: có đơn mới, đổi trạng thái đơn, tin được duyệt/từ chối, công ty được duyệt/từ chối | Người dùng | Cao |
| FR-M3-02 | Gửi email thông báo cho các sự kiện quan trọng (xác thực, đổi trạng thái đơn, kết quả duyệt) | Hệ thống | TB |
| FR-M3-03 | Xem danh sách thông báo, đánh dấu đã đọc, hiển thị số thông báo chưa đọc | Người dùng | Cao |
| FR-M3-04 | Dashboard nhà tuyển dụng: số tin, lượt xem, số đơn theo tin và theo trạng thái | Nhà tuyển dụng | TB |
| FR-M3-05 | Dashboard admin: số người dùng, số tin, số đơn, tăng trưởng theo thời gian | Admin | TB |
| FR-M3-06 | Nhắn tin giữa ứng viên và nhà tuyển dụng, chỉ khi đã có đơn ứng tuyển | Ứng viên, Nhà tuyển dụng | Thấp |
| FR-M3-07 | Đánh giá công ty (điểm và nhận xét) bởi ứng viên đã từng ứng tuyển | Ứng viên | Thấp |
| FR-M3-08 | Báo cáo tin hoặc tài khoản vi phạm | Người dùng | Thấp |
| FR-M3-09 | Xử lý báo cáo vi phạm: xem, xác nhận, bác bỏ, áp dụng biện pháp | Admin | Thấp |
| FR-M3-10 | Ghi nhật ký hoạt động quan trọng (duyệt, khóa tài khoản, gỡ tin) và cho Admin xem | Admin | Thấp |

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

## 5. Yêu cầu phi chức năng

| Mã | Nhóm | Yêu cầu |
| --- | --- | --- |
| NFR-01 | Hiệu năng | Trang thông thường tải trong tối đa 3 giây trên mạng ổn định |
| NFR-02 | Hiệu năng | Tìm kiếm và lọc việc làm trả kết quả trong tối đa 2 giây với khoảng 10.000 tin |
| NFR-03 | Hiệu năng | Hỗ trợ tối thiểu 100 người dùng truy cập đồng thời |
| NFR-04 | Bảo mật | Mật khẩu được băm bằng thuật toán an toàn (ví dụ bcrypt), tối thiểu 8 ký tự |
| NFR-05 | Bảo mật | Toàn bộ truyền tải qua HTTPS; phiên đăng nhập dùng token (JWT) có thời hạn |
| NFR-06 | Bảo mật | Chống SQL Injection, XSS, CSRF; kiểm tra và làm sạch dữ liệu đầu vào |
| NFR-07 | Bảo mật | Phân quyền chặt chẽ; CV chỉ được xem bởi chủ sở hữu và nhà tuyển dụng nhận đơn tương ứng |
| NFR-08 | Bảo mật | Khóa tạm thời đăng nhập sau 5 lần sai liên tiếp |
| NFR-09 | Khả dụng | Giao diện dễ dùng, người dùng mới hoàn thành ứng tuyển trong tối đa 5 thao tác chính |
| NFR-10 | Độ tin cậy | Hệ thống hoạt động tối thiểu 99% thời gian; sao lưu cơ sở dữ liệu định kỳ hằng ngày |
| NFR-11 | Tương thích | Chạy đúng trên Chrome, Firefox, Edge, Safari; hiển thị tốt từ màn hình 360 px |
| NFR-12 | Bảo trì | Mã nguồn theo cấu trúc module, có chú thích; tài liệu đồng bộ với hệ thống |
| NFR-13 | Mở rộng | Cho phép thêm module mới và tăng tải mà không phải thiết kế lại CSDL |
| NFR-14 | Quyền riêng tư | Chỉ thu thập dữ liệu cá nhân cần thiết; hồ sơ riêng tư không xuất hiện công khai |

## 6. Quy tắc nghiệp vụ

| Mã | Quy tắc |
| --- | --- |
| BR-01 | Email là duy nhất trong hệ thống; tài khoản chưa xác thực email không được ứng tuyển hoặc đăng tin |
| BR-02 | Nhà tuyển dụng chỉ được đăng tin khi công ty đã được Admin duyệt |
| BR-03 | Tin tuyển dụng chỉ hiển thị công khai khi ở trạng thái Đã duyệt và chưa quá hạn |
| BR-04 | Vòng đời tin: Nháp, Chờ duyệt, Đã duyệt, Bị từ chối, Đã đóng, Hết hạn |
| BR-05 | Mỗi ứng viên chỉ ứng tuyển một lần cho mỗi tin; chỉ ứng tuyển tin đang mở |
| BR-06 | Vòng đời đơn: Mới, Đã xem, Phỏng vấn, Nhận hoặc Từ chối; ứng viên có thể rút đơn trước khi có kết quả cuối |
| BR-07 | Mỗi lần đổi trạng thái đơn phải được lưu lịch sử (thời điểm, người thực hiện) |
| BR-08 | Nhà tuyển dụng chỉ xem được đơn của các tin thuộc công ty mình |
| BR-09 | Tài khoản bị khóa không thể đăng nhập; dữ liệu cũ vẫn được giữ lại |
| BR-10 | Ngành nghề, kỹ năng, tỉnh/thành đang được sử dụng chỉ được ẩn, không xóa cứng |
| BR-11 | Chỉ ứng viên đã ứng tuyển công ty mới được đánh giá công ty đó (mở rộng) |

## 7. Phụ lục

### 7.1 Ma trận actor và module

| Actor | M0 | M1 | M2 | M3 |
| --- | --- | --- | --- | --- |
| Khách | Xem danh mục | Đăng ký, đăng nhập, xem công ty | Xem, tìm kiếm, lọc việc | Không |
| Ứng viên | Xem danh mục | Hồ sơ, CV | Ứng tuyển, lưu việc, theo dõi đơn | Thông báo, nhắn tin, đánh giá |
| Nhà tuyển dụng | Xem danh mục | Hồ sơ công ty | Đăng tin, quản lý ứng viên | Thông báo, dashboard, nhắn tin |
| Admin | Quản lý đầy đủ | Duyệt công ty, quản lý tài khoản | Duyệt, gỡ tin | Dashboard, xử lý báo cáo, nhật ký |

### 7.2 Thống kê yêu cầu chức năng

| Module | Cao | TB | Thấp | Tổng |
| --- | --- | --- | --- | --- |
| M0 | 4 | 1 | 1 | 6 |
| M1 | 13 | 2 | 2 | 17 |
| M2 | 14 | 6 | 0 | 20 |
| M3 | 2 | 3 | 5 | 10 |

### 7.3 Việc cần chốt ở bước tiếp theo

- Công nghệ (tech stack) và kiến trúc triển khai: ghi trong tài liệu thiết kế hệ thống.
- Các bảng CSDL, ERD và mô tả chi tiết từng module: ghi trong tài liệu thiết kế hệ thống.
