# Thông báo cập nhật dự án trước khi merge main

Mọi người xem giúp bản cập nhật trên nhánh `feat/architecture-api-alignment` trước khi gộp vào `main`. Nhánh đã có trên GitHub, hiện chưa merge. Thay đổi gồm cả biểu mẫu nhà tuyển dụng PB-015, tích hợp API PB-014 và đợt chỉnh kiến trúc/API.

Các nội dung chính:

- Có form tạo/sửa hồ sơ công ty, lưu nháp và gửi duyệt tin tuyển dụng. Trang chủ lấy việc làm thật, có tìm kiếm, phân trang và xem chi tiết.
- Đã bổ sung đủ 24 method/đường dẫn API cốt lõi trong thiết kế: hồ sơ, danh mục, công ty, tin, ứng tuyển, thông báo, xác thực email và đặt lại mật khẩu. Các API cũ vẫn được giữ.
- Đường dẫn frontend đã đổi: CSS ở `client/src/assets/css`, UI ở `client/src/features`, API client ở `client/src/services`. Backend tách `routes → controllers → services → models`, auth/RBAC ở `middlewares/auth.py`. Mọi người đang làm nhánh riêng lưu ý sửa import và đường dẫn khi đồng bộ.
- Giữ HTML/JavaScript + FastAPI/SQLAlchemy/Alembic/MySQL. Chưa chuyển sang React/Express/Prisma như bản Word; nhóm cần thống nhất khác biệt này khi duyệt thiết kế.
- Chưa có trang Admin/ứng viên/thông báo đầy đủ. Duyệt hiện qua Swagger bằng tài khoản Admin. Duyệt công ty và duyệt tin là hai bước riêng; DRAFT là nháp, PENDING là chờ duyệt, APPROVED là đã duyệt.

Kết quả kiểm thử đã ghi nhận: 52 test backend và 21 test frontend đạt; mô phỏng merge với main tại commit `6f22a6c` không có conflict Git. Backend test dùng SQLite và SMTP giả lập, nên cần kiểm tra tiếp MySQL, SMTP và giao diện trên môi trường thật trước khi nghiệm thu.

Mỗi người giữ `.env` và dữ liệu cục bộ của mình, không chép đè bằng file mẫu. Không có migration mới trong bản cập nhật; máy mới vẫn phải khởi tạo database theo SETUP. Email cần bổ sung cấu hình SMTP và FRONTEND_URL theo `.env.example`. Hiện chưa bắt buộc xác thực email khi đăng nhập và chưa có luồng gửi lại email xác thực.

Nhờ mọi người review phần mình phụ trách: frontend kiểm tra UI/đường dẫn; M0 kiểm tra danh mục; M1 kiểm tra profile/CV và email/reset; M2 kiểm tra duyệt tin/ứng tuyển/quyền sở hữu; M3 kiểm tra thông báo/SMTP. Khi main đã merge, lưu công việc đang làm rồi pull main và cập nhật nhánh cá nhân theo cấu trúc mới.

Báo cáo chi tiết và checklist: [TEAM_CHANGE_REPORT.md](TEAM_CHANGE_REPORT.md). Cấu trúc: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md). Đối chiếu thiết kế/API: [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md). Cài đặt/chạy: [SETUP.md](SETUP.md).

Nhánh review: https://github.com/Team1-JobContact/Vieco/tree/feat/architecture-api-alignment
