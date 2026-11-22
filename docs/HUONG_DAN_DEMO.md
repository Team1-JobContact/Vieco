# Hướng dẫn demo Vieco

Tài liệu này dùng cho buổi demo và cho thành viên muốn tự kiểm tra luồng chính: công ty → tin tuyển dụng → ứng tuyển → xử lý đơn. Cách cài đặt và chạy dự án xem [SETUP](SETUP.md) và [hướng dẫn Windows](HUONG_DAN_CHAY_DU_AN.md).

## 1. Chuẩn bị

1. Chạy backend ở cổng 8000 và frontend ở cổng 5500 theo README.
2. Đã chạy `alembic upgrade head` và `python -m src.seeds.run`. Sau khi cập nhật mã nguồn có migration mới (ví dụ `0003` cho hình ảnh công ty, `0004` cho trình tạo CV), chạy lại `alembic upgrade head`. Tài khoản Admin lấy từ `ADMIN_EMAIL` và `ADMIN_PASSWORD` trong `.env`.
3. (Tùy chọn) Nạp dữ liệu demo: 10 doanh nghiệp và 43 tin tuyển dụng phủ đủ 21 ngành nghề, 5 hình thức làm việc và 5 mức kinh nghiệm. Chạy trong `source_code/server`:
   1. `python -m src.seeds.demo_companies`: tạo 10 tài khoản nhà tuyển dụng `tuyendung.<tên>@vieco.click` (mật khẩu `123345678A`, đổi bằng biến môi trường `DEMO_EMPLOYER_PASSWORD`) kèm hồ sơ công ty ở trạng thái Chờ duyệt, chưa có hình ảnh.
   2. Admin duyệt 10 công ty tại `pages/admin.html`.
   3. `python -m src.seeds.demo_jobs`: tạo và duyệt các tin tuyển dụng bằng tài khoản Admin.
   4. `python -m src.seeds.demo_media`: gắn logo, ảnh bìa và 3 ảnh không gian làm việc cho 10 công ty (ảnh trong `src/seeds/demo_media/`, nguồn và giấy phép ở `CREDITS.md`). Công ty đã có ảnh thì bỏ qua.

   Các script chạy lại nhiều lần không tạo trùng. Nội dung tin và mức lương là dữ liệu demo, không phải tin thật của doanh nghiệp. Một số ảnh không gian làm việc là ảnh minh họa chung, không phải ảnh thật của doanh nghiệp đó.
4. Chuẩn bị một tệp CV thật dạng PDF, DOC hoặc DOCX nhỏ hơn 5 MB.
5. Mở ba cửa sổ trình duyệt riêng (ví dụ một cửa sổ thường, một cửa sổ ẩn danh và một trình duyệt khác) để đăng nhập ba vai trò cùng lúc.

## 2. Các trang giao diện

Giao diện dựng theo thiết kế Figma "Vieco • Desktop". Mọi trang dùng chung header, menu trượt, bảng tìm kiếm và footer.

| Trang | Đường dẫn | Ai dùng |
| --- | --- | --- |
| Trang chủ | `index.html` | Mọi người |
| Danh sách việc làm | `pages/jobs.html` | Mọi người |
| Chi tiết việc làm và ứng tuyển | `pages/job.html?id=<id>` | Mọi người; ứng tuyển cần tài khoản ứng viên |
| Danh sách và chi tiết công ty | `pages/companies.html`, `pages/company.html?id=<id>` | Mọi người |
| Hồ sơ của tôi | `pages/profile.html` | Ứng viên |
| Hồ sơ công ty và form tin | `pages/employer.html` | Nhà tuyển dụng |
| Quản lý tin và ứng viên | `pages/employer-jobs.html` | Nhà tuyển dụng |
| Hình ảnh công ty (logo, ảnh bìa, không gian làm việc) | `pages/company-media.html` | Nhà tuyển dụng |
| Trang quản trị | `pages/admin.html` | Admin |
| Quản lý tài khoản, danh mục, nội dung, giới hạn tải tệp và nhật ký | `pages/admin.html#users`, `#categories`, `#pages`, `#settings`, `#audit` | Admin |
| Học vấn, kinh nghiệm, kỹ năng và ảnh đại diện | `pages/profile.html#history`, `pages/profile.html#settings` | Ứng viên |
| Tạo CV trực tuyến: chọn mẫu, thêm ảnh, xem trước A4, tải PDF, lưu vào CV của tôi, tạo bằng AI | `pages/cv-builder.html` (`?template=elegant`, `modern`, `minimal`; `?cv=<id>` để sửa CV đã lưu; `?ai=1` mở sẵn hộp AI) | Mọi người tạo và tải PDF; lưu CV và dùng AI cần tài khoản ứng viên |
| Trang nội dung đã xuất bản | `pages/content.html?slug=gioi-thieu`, `?slug=dieu-khoan`, `?slug=faq` | Mọi người |
| Thông báo | `pages/notifications.html` | Người đã đăng nhập |
| Giới thiệu cho nhà tuyển dụng, Thư viện CV, Liên hệ | `pages/for-employers.html`, `pages/cv-library.html`, `pages/contact.html` | Mọi người |

## 3. Kịch bản demo

| Bước | Vai trò | Thao tác | Kết quả mong đợi |
| --- | --- | --- | --- |
| 1 | Khách | Mở trang chủ, mở Menu và Tìm kiếm | Trang chủ hiển thị; chưa có tin thì báo "Chưa có việc làm đang tuyển" |
| 2 | Nhà tuyển dụng | Đăng ký tài khoản nhà tuyển dụng, đăng nhập, tạo hồ sơ công ty tại `pages/employer.html` | Công ty ở trạng thái Chờ duyệt; trang quản lý tin báo đang chờ duyệt |
| 3 | Admin | Đăng nhập, mở `pages/admin.html`, bấm Từ chối và nhập lý do | Không nhập đủ 10 ký tự thì không gửi được; công ty chuyển Bị từ chối |
| 4 | Nhà tuyển dụng | Xem lý do từ chối, sửa hồ sơ, gửi duyệt lại | Công ty trở lại Chờ duyệt |
| 5 | Admin | Bấm Duyệt công ty | Công ty Đã duyệt và xuất hiện ở trang Công ty |
| 5a | Nhà tuyển dụng | Mở `pages/company-media.html`, tải logo, ảnh bìa và ảnh không gian làm việc | Ảnh hiển thị ở trang công ty, thẻ công ty và tin tuyển dụng; tệp không phải JPG/PNG/WEBP bị từ chối |
| 6 | Nhà tuyển dụng | Tạo tin tại `pages/employer.html#job`, lưu nháp rồi gửi duyệt | Tin ở trạng thái Chờ duyệt, chưa hiển thị công khai |
| 7 | Admin | Mở tab Duyệt tin tuyển dụng, bấm Duyệt | Tin xuất hiện ở trang chủ và trang Việc làm |
| 8 | Khách | Tìm theo tên vị trí, tên công ty hoặc kỹ năng; lọc và sắp xếp | Số kết quả và danh sách thay đổi theo bộ lọc |
| 9 | Ứng viên | Đăng ký, mở tin, bấm Ứng tuyển ngay, tải CV và gửi | Hiện "Ứng tuyển thành công!"; nút đổi thành "Đã ứng tuyển" |
| 10 | Ứng viên | Thử tải tệp không phải PDF/DOC/DOCX hoặc lớn hơn 5 MB | Bị từ chối kèm thông báo lỗi |
| 10a | Ứng viên | Ở Trang chủ, mục Top CV nổi bật, bấm Sử dụng mẫu; nhập thông tin, thêm ảnh, đổi mẫu, Tải PDF rồi Lưu vào CV của tôi | Bản xem trước cập nhật khi gõ và tự chia trang A4; tệp PDF tải về máy; CV hiện trong mục CV của tôi với nút Chỉnh sửa và chọn được khi ứng tuyển |
| 10b | Ứng viên | Trong trang tạo CV bấm Tạo bằng AI, nhập thông tin tự do rồi bấm Tạo CV | Có `ANTHROPIC_API_KEY`: biểu mẫu và bản xem trước được điền sẵn để chỉnh lại. Chưa có khóa: báo tính năng AI chưa bật |
| 11 | Nhà tuyển dụng | Mở `pages/employer-jobs.html`, bấm Ứng viên, Xem hồ sơ, tải CV, Mời phỏng vấn | Đơn tự chuyển Đang xem xét khi mở; sau đó chuyển Mời phỏng vấn |
| 12 | Ứng viên | Mở Hồ sơ của tôi | Chuông thông báo có số chưa đọc; đơn hiển thị trạng thái mới và lịch sử xử lý |
| 13 | Ứng viên | Ứng tuyển một tin khác rồi rút đơn | Đơn chuyển Đã rút; đơn đã được mời phỏng vấn không còn nút rút |
| 14 | Nhà tuyển dụng | Đóng tin | Tin biến mất khỏi trang công khai; đơn đã nộp vẫn còn |

## 4. Điểm kiểm tra phân quyền

- Chưa đăng nhập mà mở `pages/profile.html`, `pages/admin.html` hoặc `pages/employer-jobs.html` thì bị chuyển sang trang đăng nhập.
- Đăng nhập sai vai trò thì trang báo "Bạn không có quyền truy cập trang này"; API trả 403.
- Nhà tuyển dụng của công ty khác không xem được đơn và không tải được CV (API trả 404).
- CV chỉ tải được qua API có kiểm tra quyền; thư mục `uploads/` không được phục vụ công khai.

## 5. Kiểm thử tự động

```powershell
cd source_code/server
python -m pytest
```

Bộ test backend gồm luồng end-to-end đăng ký → hồ sơ → duyệt công ty → đăng tin → duyệt tin → ứng tuyển → xử lý đơn và ma trận phân quyền, trong `tests/test_workflows.py`.

```powershell
cd source_code/client
npm install
npm test
```

Test giao diện chạy bằng Node.js và jsdom.

## 6. Giới hạn hiện tại

- CV tạo trực tuyến được lưu thành PDF dạng ảnh (mỗi trang A4 là một ảnh nét gấp đôi), nên không bôi đen hay sao chép được chữ trong PDF. Nội dung gốc được lưu kèm để mở lại chỉnh sửa. Cập nhật một CV đã dùng để ứng tuyển sẽ tạo bản mới; đơn đã nộp vẫn giữ bản cũ.
- Tạo CV bằng AI cần `ANTHROPIC_API_KEY` trong `server/.env` (tùy chọn `AI_CV_MODEL`, mặc định `claude-opus-5-5`). Mỗi tài khoản tối đa 10 lượt mỗi giờ. Nội dung người dùng nhập được gửi tới Claude của Anthropic. AI chỉ sắp xếp và diễn đạt lại thông tin được nhập, người dùng cần đọc lại trước khi lưu.
- Trang tạo CV không có trong bản Figma; bố cục dùng chung màu, chữ và kiểu khối của các trang khác.
- Form Liên hệ chưa có API tiếp nhận; trang mở ứng dụng email của người dùng với nội dung đã điền.
- Hình ảnh công ty do nhà tuyển dụng tự tải lên (JPG, PNG, WEBP; logo tối đa 2 MB, ảnh bìa và ảnh không gian làm việc tối đa 5 MB, tối đa 6 ảnh). Công ty chưa tải ảnh thì hiển thị tên viết tắt, không dùng ảnh mặc định. Thay ảnh không yêu cầu Admin duyệt lại.
- Liên kết website dài hơn 32 ký tự chỉ hiển thị chữ "Fanpage" (mạng xã hội) hoặc "Website", bấm vào mở liên kết ở thẻ mới.
- Chưa có theo dõi công ty, đánh giá công ty và lịch hẹn phỏng vấn như trong bản thiết kế.
- Trang đăng nhập, đăng ký, khôi phục tài khoản và form hồ sơ công ty/tin tuyển dụng dùng chung header, footer, bảng màu và kiểu khối với các trang khác qua `src/assets/css/vieco-sync.css`. Bố cục bên trong các trang này giữ nguyên vì thiết kế Figma không có màn hình tương ứng.
- Riêng trang đăng nhập và đăng ký có phong cách bo tròn, điểm nhấn vàng trên nền xanh trong `src/assets/css/auth-modern.css`; các trang khác vẫn giữ góc vuông theo Figma.
- Logo và favicon nằm trong `src/assets/images/brand/` (logo đầy đủ, biểu tượng chữ V, favicon 32/64px và icon cho iPhone).
- Thiết kế Figma chỉ có bản desktop; bản di động do nhóm tự co giãn bố cục.
