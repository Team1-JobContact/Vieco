"""Dữ liệu danh mục cơ bản. Sửa/thêm tại đây rồi chạy lại seed (seed idempotent)."""

ROLES = [
    ("ADMIN", "Quản trị viên hệ thống"),
    ("CANDIDATE", "Ứng viên tìm việc"),
    ("EMPLOYER", "Nhà tuyển dụng"),
]

# (tên, slug)
INDUSTRIES = [
    ("Công nghệ thông tin / Phần mềm", "cong-nghe-thong-tin"),
    ("Kinh doanh / Bán hàng", "kinh-doanh-ban-hang"),
    ("Marketing / Truyền thông / Quảng cáo", "marketing-truyen-thong"),
    ("Kế toán / Kiểm toán", "ke-toan-kiem-toan"),
    ("Tài chính / Ngân hàng / Bảo hiểm", "tai-chinh-ngan-hang"),
    ("Nhân sự / Hành chính", "nhan-su-hanh-chinh"),
    ("Thiết kế / Sáng tạo", "thiet-ke-sang-tao"),
    ("Giáo dục / Đào tạo", "giao-duc-dao-tao"),
    ("Y tế / Dược phẩm", "y-te-duoc-pham"),
    ("Sản xuất / Vận hành nhà máy", "san-xuat-van-hanh"),
    ("Xây dựng / Kiến trúc", "xay-dung-kien-truc"),
    ("Bất động sản", "bat-dong-san"),
    ("Logistics / Vận tải / Kho vận", "logistics-van-tai"),
    ("Du lịch / Nhà hàng / Khách sạn", "du-lich-nha-hang-khach-san"),
    ("Chăm sóc khách hàng", "cham-soc-khach-hang"),
    ("Pháp lý / Luật", "phap-ly-luat"),
    ("Điện / Điện tử / Cơ khí", "dien-dien-tu-co-khi"),
    ("Nông nghiệp / Thực phẩm", "nong-nghiep-thuc-pham"),
    ("Thương mại điện tử", "thuong-mai-dien-tu"),
    ("Biên phiên dịch / Ngoại ngữ", "bien-phien-dich-ngoai-ngu"),
    ("Khác", "khac"),
]

# (tên kỹ năng, slug ngành gợi ý hoặc None). Tên kỹ năng là duy nhất toàn hệ thống.
SKILLS = [
    # CNTT
    ("Python", "cong-nghe-thong-tin"), ("Java", "cong-nghe-thong-tin"),
    ("JavaScript", "cong-nghe-thong-tin"), ("TypeScript", "cong-nghe-thong-tin"),
    ("C#", "cong-nghe-thong-tin"), ("C++", "cong-nghe-thong-tin"), ("PHP", "cong-nghe-thong-tin"),
    ("Go", "cong-nghe-thong-tin"), ("HTML/CSS", "cong-nghe-thong-tin"),
    ("React", "cong-nghe-thong-tin"), ("Vue.js", "cong-nghe-thong-tin"),
    ("Node.js", "cong-nghe-thong-tin"), ("FastAPI", "cong-nghe-thong-tin"),
    ("Django", "cong-nghe-thong-tin"), ("Spring Boot", "cong-nghe-thong-tin"),
    ("SQL", "cong-nghe-thong-tin"), ("MySQL", "cong-nghe-thong-tin"),
    ("PostgreSQL", "cong-nghe-thong-tin"), ("MongoDB", "cong-nghe-thong-tin"),
    ("Docker", "cong-nghe-thong-tin"), ("Git", "cong-nghe-thong-tin"),
    ("Linux", "cong-nghe-thong-tin"), ("AWS", "cong-nghe-thong-tin"),
    ("Kiểm thử phần mềm (Testing)", "cong-nghe-thong-tin"),
    ("Phân tích dữ liệu", "cong-nghe-thong-tin"), ("Machine Learning", "cong-nghe-thong-tin"),
    ("Android", "cong-nghe-thong-tin"), ("iOS", "cong-nghe-thong-tin"),
    ("Phân tích nghiệp vụ (BA)", "cong-nghe-thong-tin"),
    # Kinh doanh / Marketing
    ("Bán hàng B2B", "kinh-doanh-ban-hang"), ("Đàm phán", "kinh-doanh-ban-hang"),
    ("Quản lý khách hàng (CRM)", "kinh-doanh-ban-hang"),
    ("SEO", "marketing-truyen-thong"), ("Google Ads", "marketing-truyen-thong"),
    ("Facebook Ads", "marketing-truyen-thong"), ("Content Marketing", "marketing-truyen-thong"),
    ("Viết nội dung (Copywriting)", "marketing-truyen-thong"),
    # Kế toán / Tài chính / Nhân sự
    ("Kế toán tổng hợp", "ke-toan-kiem-toan"), ("Báo cáo thuế", "ke-toan-kiem-toan"),
    ("Phân tích tài chính", "tai-chinh-ngan-hang"),
    ("Tuyển dụng", "nhan-su-hanh-chinh"), ("Tiền lương và chế độ (C&B)", "nhan-su-hanh-chinh"),
    # Thiết kế
    ("Photoshop", "thiet-ke-sang-tao"), ("Illustrator", "thiet-ke-sang-tao"),
    ("Figma", "thiet-ke-sang-tao"), ("UI/UX", "thiet-ke-sang-tao"),
    ("Dựng video", "thiet-ke-sang-tao"),
    # Khác
    ("AutoCAD", "xay-dung-kien-truc"), ("Vận hành máy CNC", "dien-dien-tu-co-khi"),
    ("Quản lý kho", "logistics-van-tai"), ("Giảng dạy", "giao-duc-dao-tao"),
    ("Tiếng Anh", "bien-phien-dich-ngoai-ngu"), ("Tiếng Nhật", "bien-phien-dich-ngoai-ngu"),
    ("Tiếng Hàn", "bien-phien-dich-ngoai-ngu"), ("Tiếng Trung", "bien-phien-dich-ngoai-ngu"),
    # Kỹ năng chung (không gắn ngành)
    ("Tin học văn phòng", None), ("Excel", None), ("Giao tiếp", None),
    ("Làm việc nhóm", None), ("Quản lý thời gian", None), ("Quản lý dự án", None),
    ("Giải quyết vấn đề", None), ("Thuyết trình", None), ("Lãnh đạo nhóm", None),
]

# 34 đơn vị hành chính cấp tỉnh (sau sắp xếp 2025). `code` là mã nội bộ của hệ thống,
# không phải mã hành chính chính thức. Nên đối chiếu lại danh sách trước khi dùng thật.
PROVINCES = [
    ("Hà Nội", "HN"), ("TP. Hồ Chí Minh", "HCM"), ("Hải Phòng", "HP"), ("Đà Nẵng", "DN"),
    ("Cần Thơ", "CT"), ("Huế", "HUE"),
    ("Tuyên Quang", "TQ"), ("Lào Cai", "LC"), ("Thái Nguyên", "TN"), ("Phú Thọ", "PT"),
    ("Bắc Ninh", "BN"), ("Hưng Yên", "HY"), ("Ninh Bình", "NB"), ("Quảng Trị", "QT"),
    ("Quảng Ngãi", "QNG"), ("Gia Lai", "GL"), ("Khánh Hòa", "KH"), ("Lâm Đồng", "LD"),
    ("Đắk Lắk", "DL"), ("Đồng Nai", "DNA"), ("Tây Ninh", "TNI"), ("Vĩnh Long", "VL"),
    ("Đồng Tháp", "DT"), ("Cà Mau", "CM"), ("An Giang", "AG"), ("Điện Biên", "DB"),
    ("Lai Châu", "LCH"), ("Sơn La", "SL"), ("Lạng Sơn", "LS"), ("Quảng Ninh", "QN"),
    ("Thanh Hóa", "TH"), ("Nghệ An", "NA"), ("Hà Tĩnh", "HT"), ("Cao Bằng", "CB"),
]

# (khóa, giá trị, mô tả) — theo SRS FR-M0-04, NFR-08, UC-01, UC-02
SYSTEM_SETTINGS = [
    ("job_default_days", "30", "Thời hạn nộp hồ sơ mặc định của tin tuyển dụng (ngày)"),
    ("cv_max_size_mb", "5", "Dung lượng tối đa mỗi tệp CV (MB)"),
    ("cv_max_count", "5", "Số CV tối đa mỗi hồ sơ ứng viên"),
    ("cv_allowed_extensions", "pdf,doc,docx", "Định dạng CV được chấp nhận"),
    ("image_max_size_mb", "2", "Dung lượng tối đa logo/ảnh đại diện (MB)"),
    ("email_from", "noreply@jobcontact.vn", "Địa chỉ email gửi đi"),
    ("login_max_failed_attempts", "5", "Số lần đăng nhập sai liên tiếp trước khi khóa tạm thời (NFR-08)"),
    ("login_lock_minutes", "15", "Thời gian khóa đăng nhập tạm thời (phút)"),
    ("email_verification_hours", "24", "Thời hạn liên kết xác thực email (giờ)"),
    ("password_reset_hours", "1", "Thời hạn liên kết đặt lại mật khẩu (giờ)"),
    ("job_expiring_soon_days", "3", "Số ngày trước hạn để nhắc gia hạn tin"),
]

STATIC_PAGES = [
    ("gioi-thieu", "Giới thiệu JobContact",
     "JobContact là nền tảng kết nối ứng viên với nhà tuyển dụng. Nhà tuyển dụng đăng tin và quản lý hồ sơ "
     "ứng tuyển; ứng viên tạo hồ sơ, tìm việc và ứng tuyển trực tuyến.\n\n(Nội dung mẫu, Admin có thể chỉnh sửa.)"),
    ("dieu-khoan", "Điều khoản sử dụng",
     "Bằng việc sử dụng JobContact, bạn đồng ý cung cấp thông tin chính xác, không đăng nội dung vi phạm pháp "
     "luật và tuân thủ các quy định của hệ thống.\n\n(Nội dung mẫu, cần thay bằng điều khoản chính thức.)"),
    ("faq", "Câu hỏi thường gặp",
     "1. Làm sao để ứng tuyển? Đăng nhập tài khoản ứng viên, tải CV và chọn Ứng tuyển ở tin mong muốn.\n"
     "2. Vì sao tin của tôi chưa hiển thị? Tin cần được Admin duyệt và công ty phải được duyệt trước.\n"
     "3. Tôi quên mật khẩu? Chọn Quên mật khẩu để nhận liên kết đặt lại qua email.\n\n(Nội dung mẫu.)"),
]
