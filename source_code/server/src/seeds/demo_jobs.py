"""Tạo tin tuyển dụng mẫu cho 10 công ty demo (xem demo_companies.py) và duyệt bằng tài khoản Admin.

Chạy từ thư mục server/ (sau khi Admin đã duyệt 10 công ty):  python -m src.seeds.demo_jobs

- Mỗi công ty 4–5 tin; toàn bộ tin phủ đủ 21 ngành nghề, 5 hình thức làm việc và 5 mức kinh nghiệm
  để mọi lựa chọn trong bộ lọc tìm kiếm đều có kết quả.
- Đi qua đúng nghiệp vụ: JobCreate/create_job (action="submit") rồi approve_job bằng tài khoản Admin
  (ghi nhật ký và thông báo như khi thao tác trên giao diện).
- Idempotent: công ty đã có tin cùng tiêu đề thì bỏ qua. Hạn nộp tính từ ngày chạy script.
- Mức lương và nội dung chỉ là dữ liệu demo, không phải tin tuyển dụng thật của doanh nghiệp.
"""
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from src.config.database import SessionLocal
from src.models import Industry, Province, Role, Skill, User
from src.models.company import Company, CompanyMember
from src.models.recruitment import Job
from src.schemas.job import JobCreate
from src.services import job_service

M = 1_000_000

# Phúc lợi chung theo từng công ty (email chủ sở hữu → danh sách dòng).
BENEFITS = {
    "fpt": ["Lương tháng 13 và thưởng theo kết quả kinh doanh", "Bảo hiểm sức khỏe FPT Care cho nhân viên",
            "Đào tạo nội bộ và hỗ trợ thi chứng chỉ quốc tế", "Cơ hội onsite tại Nhật Bản, Mỹ, châu Âu"],
    "viettel": ["Thu nhập cạnh tranh, xét tăng lương định kỳ", "Đầy đủ BHXH, BHYT, BHTN theo quy định",
                "Môi trường kỷ luật, chuyên nghiệp, nhiều dự án quy mô lớn", "Khám sức khỏe định kỳ hằng năm"],
    "vinamilk": ["Lương tháng 13 và thưởng hiệu quả công việc", "Bảo hiểm sức khỏe cho nhân viên",
                 "Sản phẩm của công ty hằng tháng", "Lộ trình đào tạo và phát triển rõ ràng"],
    "vietcombank": ["Thu nhập theo quy chế lương của ngân hàng", "Đầy đủ chế độ bảo hiểm và phúc lợi",
                    "Chương trình đào tạo nghiệp vụ bài bản", "Cơ hội luân chuyển và thăng tiến"],
    "momo": ["Thưởng hiệu suất và gói cổ phiếu ưu đãi (ESOP)", "Bảo hiểm sức khỏe cao cấp",
             "Làm việc linh hoạt, hỗ trợ thiết bị làm việc", "Ngân sách học tập và hội thảo hằng năm"],
    "tiki": ["Lương tháng 13, thưởng theo hiệu suất", "Bảo hiểm sức khỏe cho nhân viên",
             "Ưu đãi mua sắm trên Tiki", "Môi trường trẻ, năng động"],
    "ghn": ["Thu nhập ổn định, thưởng theo sản lượng", "Đầy đủ BHXH, BHYT, BHTN theo quy định",
            "Phụ cấp xăng xe và điện thoại", "Cơ hội thăng tiến lên quản lý bưu cục"],
    "vietnamairlines": ["Thu nhập theo quy chế của Tổng công ty", "Chế độ vé máy bay ưu đãi cho nhân viên",
                        "Đào tạo chuyên sâu theo tiêu chuẩn ngành hàng không", "Đầy đủ bảo hiểm và khám sức khỏe định kỳ"],
    "longchau": ["Lương cứng cộng thưởng doanh số", "Đào tạo chuyên môn dược định kỳ",
                 "Ưu đãi mua thuốc và tiêm chủng cho nhân viên", "Lộ trình lên quản lý nhà thuốc"],
    "coteccons": ["Lương tháng 13 và thưởng dự án", "Phụ cấp công trình, hỗ trợ chỗ ở khi đi tỉnh",
                  "Bảo hiểm tai nạn 24/7", "Làm việc tại các công trình quy mô lớn"],
}

# (công ty, tiêu đề, ngành, tỉnh, địa chỉ làm việc, hình thức, kinh nghiệm, lương min, lương max (triệu VND),
#  số lượng, số ngày đến hạn, kỹ năng, mô tả, yêu cầu)
JOBS = [
    # ---------- FPT ----------
    ("fpt", "Lập trình viên Python (Backend)", "cong-nghe-thong-tin", "HN",
     "Tòa nhà FPT, số 10 Phạm Văn Bạch, Cầu Giấy, Hà Nội", "FULL_TIME", "FROM_1_TO_3", 18, 30, 5, 30,
     ["Python", "FastAPI", "SQL", "Docker", "Git"],
     ["Phát triển API và dịch vụ backend cho các dự án chuyển đổi số", "Thiết kế cơ sở dữ liệu và tối ưu truy vấn",
      "Viết unit test, tham gia review code", "Phối hợp với đội frontend và QA để bàn giao tính năng"],
     ["Tối thiểu 1 năm kinh nghiệm lập trình Python", "Hiểu RESTful API, có kinh nghiệm với FastAPI hoặc Django",
      "Thành thạo SQL, biết Docker và Git", "Đọc hiểu tài liệu tiếng Anh"]),
    ("fpt", "Thực tập sinh Lập trình Java", "cong-nghe-thong-tin", "DN",
     "FPT Complex, Khu đô thị FPT City, Ngũ Hành Sơn, Đà Nẵng", "INTERNSHIP", "NONE", 3, 5, 20, 25,
     ["Java", "Spring Boot", "SQL", "Git"],
     ["Tham gia chương trình đào tạo Fresher 3 tháng", "Thực hành trên dự án thật dưới sự hướng dẫn của mentor",
      "Có cơ hội trở thành nhân viên chính thức sau kỳ thực tập"],
     ["Sinh viên năm cuối hoặc mới tốt nghiệp ngành CNTT", "Nắm vững Java và lập trình hướng đối tượng",
      "Có thể làm việc toàn thời gian tại Đà Nẵng"]),
    ("fpt", "Giảng viên Lập trình Web (bán thời gian)", "giao-duc-dao-tao", "HN",
     "Trường Cao đẳng FPT Polytechnic, Hà Nội", "PART_TIME", "FROM_3_TO_5", 15, 25, 3, 40,
     ["Giảng dạy", "JavaScript", "HTML/CSS", "Thuyết trình"],
     ["Giảng dạy các môn lập trình web cho sinh viên cao đẳng", "Xây dựng bài giảng, bài tập và đề thi",
      "Hướng dẫn sinh viên làm dự án cuối kỳ"],
     ["Tối thiểu 3 năm kinh nghiệm phát triển web", "Có kỹ năng truyền đạt tốt, ưu tiên đã từng giảng dạy",
      "Có thể dạy các ca tối trong tuần"]),
    ("fpt", "Phiên dịch viên tiếng Nhật (IT Comtor)", "bien-phien-dich-ngoai-ngu", "HN",
     "FPT Software, Khu Công nghệ cao Hòa Lạc, Hà Nội", "FULL_TIME", "FROM_1_TO_3", 20, 35, 4, 35,
     ["Tiếng Nhật", "Giao tiếp", "Tin học văn phòng"],
     ["Phiên dịch trong các cuộc họp giữa đội dự án và khách hàng Nhật Bản", "Biên dịch tài liệu đặc tả, báo cáo tiến độ",
      "Hỗ trợ trao đổi email và quản lý câu hỏi Q&A với khách hàng"],
     ["Tiếng Nhật N2 trở lên", "Có ít nhất 1 năm làm Comtor hoặc phiên dịch", "Ưu tiên có hiểu biết cơ bản về phần mềm"]),
    ("fpt", "Chuyên viên Tuyển dụng IT", "nhan-su-hanh-chinh", "HN",
     "Tòa nhà FPT, số 10 Phạm Văn Bạch, Cầu Giấy, Hà Nội", "FULL_TIME", "FROM_1_TO_3", 14, 22, 2, 30,
     ["Tuyển dụng", "Giao tiếp", "Excel"],
     ["Tìm kiếm và sàng lọc ứng viên cho các vị trí kỹ thuật", "Tổ chức phỏng vấn, phối hợp với quản lý dự án",
      "Xây dựng thương hiệu tuyển dụng trên các kênh trực tuyến"],
     ["Tối thiểu 1 năm kinh nghiệm tuyển dụng, ưu tiên mảng IT", "Kỹ năng giao tiếp và đàm phán tốt",
      "Thành thạo Excel và các nền tảng tuyển dụng"]),
    # ---------- Viettel ----------
    ("viettel", "Kỹ sư DevOps", "cong-nghe-thong-tin", "HN",
     "Lô D26, Khu đô thị mới Cầu Giấy, Cầu Giấy, Hà Nội", "FULL_TIME", "FROM_3_TO_5", 30, 50, 3, 30,
     ["Docker", "Linux", "AWS", "Git"],
     ["Xây dựng và vận hành hệ thống CI/CD cho các sản phẩm số", "Quản trị hạ tầng container và điện toán đám mây",
      "Giám sát, tối ưu hiệu năng và độ sẵn sàng của hệ thống"],
     ["Tối thiểu 3 năm kinh nghiệm DevOps hoặc quản trị hệ thống", "Thành thạo Linux, Docker, Kubernetes",
      "Có kinh nghiệm với một nền tảng cloud (AWS, GCP hoặc Viettel Cloud)"]),
    ("viettel", "Kỹ sư Điện tử Viễn thông", "dien-dien-tu-co-khi", "HN",
     "Viettel High Tech, Khu Công nghệ cao Hòa Lạc, Hà Nội", "FULL_TIME", "FROM_1_TO_3", 18, 30, 5, 45,
     ["Giải quyết vấn đề", "Làm việc nhóm", "Tiếng Anh"],
     ["Nghiên cứu, thiết kế và thử nghiệm thiết bị viễn thông", "Tham gia kiểm thử và tối ưu thiết bị mạng 4G/5G",
      "Viết tài liệu kỹ thuật cho sản phẩm"],
     ["Tốt nghiệp Điện tử Viễn thông hoặc ngành liên quan", "Có ít nhất 1 năm kinh nghiệm thiết kế phần cứng hoặc RF",
      "Đọc hiểu tài liệu kỹ thuật tiếng Anh"]),
    ("viettel", "Nhân viên Kinh doanh Dịch vụ Doanh nghiệp", "kinh-doanh-ban-hang", "HP",
     "Viettel Hải Phòng, TP. Hải Phòng", "FULL_TIME", "UNDER_1", 10, 20, 6, 20,
     ["Bán hàng B2B", "Đàm phán", "Quản lý khách hàng (CRM)"],
     ["Tư vấn giải pháp viễn thông, CNTT cho khách hàng doanh nghiệp", "Tìm kiếm khách hàng mới và chăm sóc khách hàng hiện có",
      "Lập báo cáo doanh số hằng tuần"],
     ["Tốt nghiệp cao đẳng trở lên", "Kỹ năng giao tiếp và thuyết phục tốt", "Chấp nhận ứng viên mới đi làm, sẽ được đào tạo"]),
    ("viettel", "Chuyên viên Pháp chế", "phap-ly-luat", "HN",
     "Lô D26, Khu đô thị mới Cầu Giấy, Cầu Giấy, Hà Nội", "FULL_TIME", "FROM_3_TO_5", None, None, 1, 35,
     ["Giải quyết vấn đề", "Tiếng Anh"],
     ["Soạn thảo, rà soát hợp đồng thương mại trong và ngoài nước", "Tư vấn pháp lý cho các đơn vị kinh doanh",
      "Theo dõi và cập nhật quy định pháp luật về viễn thông, CNTT"],
     ["Tốt nghiệp Cử nhân Luật", "Tối thiểu 3 năm kinh nghiệm pháp chế doanh nghiệp", "Tiếng Anh pháp lý tốt"]),
    # ---------- Vinamilk ----------
    ("vinamilk", "Kỹ sư Vận hành Dây chuyền Sản xuất", "san-xuat-van-hanh", "NA",
     "Nhà máy Sữa Nghệ An, tỉnh Nghệ An", "FULL_TIME", "FROM_1_TO_3", 15, 22, 4, 30,
     ["Giải quyết vấn đề", "Làm việc nhóm", "Excel"],
     ["Vận hành và giám sát dây chuyền chế biến sữa", "Theo dõi thông số kỹ thuật, xử lý sự cố trong ca",
      "Đề xuất cải tiến năng suất và chất lượng"],
     ["Tốt nghiệp Công nghệ Thực phẩm, Cơ khí hoặc Tự động hóa", "Có ít nhất 1 năm làm việc trong nhà máy",
      "Sẵn sàng làm việc theo ca"]),
    ("vinamilk", "Chuyên viên Nghiên cứu Phát triển Sản phẩm", "nong-nghiep-thuc-pham", "HCM",
     "Số 10 Tân Trào, phường Tân Phú, Quận 7, TP. Hồ Chí Minh", "FULL_TIME", "FROM_3_TO_5", 20, 35, 2, 40,
     ["Phân tích dữ liệu", "Tiếng Anh", "Giải quyết vấn đề"],
     ["Nghiên cứu công thức sản phẩm sữa và đồ uống mới", "Thử nghiệm mẫu, đánh giá cảm quan và độ ổn định",
      "Phối hợp với Marketing để đưa sản phẩm ra thị trường"],
     ["Tốt nghiệp Công nghệ Thực phẩm hoặc Hóa sinh", "Tối thiểu 3 năm kinh nghiệm R&D thực phẩm", "Tiếng Anh đọc hiểu tốt"]),
    ("vinamilk", "Chuyên viên Marketing Thương hiệu", "marketing-truyen-thong", "HCM",
     "Số 10 Tân Trào, phường Tân Phú, Quận 7, TP. Hồ Chí Minh", "FULL_TIME", "FROM_3_TO_5", 25, 40, 2, 30,
     ["Content Marketing", "Facebook Ads", "Thuyết trình"],
     ["Xây dựng kế hoạch truyền thông cho nhãn hàng", "Làm việc với agency triển khai chiến dịch",
      "Đo lường hiệu quả và tối ưu ngân sách marketing"],
     ["Tối thiểu 3 năm kinh nghiệm Brand Marketing ngành hàng tiêu dùng nhanh", "Tư duy phân tích và sáng tạo",
      "Kỹ năng thuyết trình tốt"]),
    ("vinamilk", "Nhân viên Kế toán Tổng hợp", "ke-toan-kiem-toan", "HCM",
     "Số 10 Tân Trào, phường Tân Phú, Quận 7, TP. Hồ Chí Minh", "FULL_TIME", "FROM_1_TO_3", 13, 18, 2, 25,
     ["Kế toán tổng hợp", "Báo cáo thuế", "Excel"],
     ["Hạch toán nghiệp vụ kế toán phát sinh", "Lập báo cáo thuế và báo cáo tài chính định kỳ",
      "Đối chiếu công nợ với khách hàng và nhà cung cấp"],
     ["Tốt nghiệp Kế toán, Kiểm toán", "Tối thiểu 1 năm kinh nghiệm kế toán tổng hợp", "Thành thạo Excel và phần mềm kế toán"]),
    # ---------- Vietcombank ----------
    ("vietcombank", "Chuyên viên Quan hệ Khách hàng Cá nhân", "tai-chinh-ngan-hang", "HN",
     "198 Trần Quang Khải, Hoàn Kiếm, Hà Nội", "FULL_TIME", "UNDER_1", 12, 20, 10, 30,
     ["Giao tiếp", "Quản lý khách hàng (CRM)", "Bán hàng B2B"],
     ["Tư vấn sản phẩm tiền gửi, thẻ, cho vay cho khách hàng cá nhân", "Phát triển và chăm sóc danh mục khách hàng",
      "Thẩm định hồ sơ vay theo quy định"],
     ["Tốt nghiệp đại học khối Kinh tế, Tài chính, Ngân hàng", "Kỹ năng giao tiếp tốt",
      "Chấp nhận ứng viên mới tốt nghiệp có định hướng ngân hàng"]),
    ("vietcombank", "Giao dịch viên", "tai-chinh-ngan-hang", "CT",
     "Vietcombank Chi nhánh Cần Thơ, TP. Cần Thơ", "FULL_TIME", "NONE", 9, 14, 6, 20,
     ["Giao tiếp", "Tin học văn phòng"],
     ["Thực hiện giao dịch nộp, rút, chuyển tiền tại quầy", "Mở tài khoản, phát hành thẻ cho khách hàng",
      "Giới thiệu sản phẩm dịch vụ của ngân hàng"],
     ["Tốt nghiệp đại học chính quy", "Ngoại hình ưa nhìn, giọng nói chuẩn", "Cẩn thận, trung thực"]),
    ("vietcombank", "Kiểm toán viên Nội bộ", "ke-toan-kiem-toan", "HN",
     "198 Trần Quang Khải, Hoàn Kiếm, Hà Nội", "FULL_TIME", "OVER_5", 35, 55, 2, 45,
     ["Phân tích tài chính", "Excel", "Tiếng Anh"],
     ["Kiểm toán hoạt động tín dụng, vận hành và tuân thủ tại các chi nhánh", "Đánh giá hệ thống kiểm soát nội bộ",
      "Lập báo cáo kiểm toán và kiến nghị khắc phục"],
     ["Tối thiểu 5 năm kinh nghiệm kiểm toán hoặc kiểm soát nội bộ ngân hàng", "Ưu tiên có chứng chỉ ACCA, CPA, CIA",
      "Sẵn sàng đi công tác"]),
    ("vietcombank", "Chuyên viên Phân tích Dữ liệu", "cong-nghe-thong-tin", "HN",
     "198 Trần Quang Khải, Hoàn Kiếm, Hà Nội", "CONTRACT", "FROM_1_TO_3", 25, 40, 2, 30,
     ["SQL", "Python", "Phân tích dữ liệu"],
     ["Xây dựng báo cáo và dashboard phục vụ quản trị", "Phân tích hành vi khách hàng trên ngân hàng số",
      "Làm sạch và chuẩn hóa dữ liệu từ nhiều nguồn"],
     ["Tối thiểu 1 năm kinh nghiệm phân tích dữ liệu", "Thành thạo SQL, biết Python hoặc công cụ BI",
      "Hợp đồng 12 tháng, có thể gia hạn"]),
    # ---------- MoMo ----------
    ("momo", "Senior Backend Engineer (Go)", "cong-nghe-thong-tin", "HCM",
     "Tòa nhà Phú Mỹ Hưng, số 8 Hoàng Văn Thái, Quận 7, TP. Hồ Chí Minh", "FULL_TIME", "OVER_5", 50, 80, 3, 30,
     ["Go", "MySQL", "Docker", "Linux"],
     ["Thiết kế và phát triển hệ thống thanh toán chịu tải lớn", "Dẫn dắt kỹ thuật và review code cho đội",
      "Đảm bảo độ ổn định, bảo mật của dịch vụ"],
     ["Tối thiểu 5 năm kinh nghiệm phát triển backend", "Thành thạo Go hoặc Java, hiểu hệ thống phân tán",
      "Có kinh nghiệm với message queue và cache"]),
    ("momo", "Product Designer (UI/UX)", "thiet-ke-sang-tao", "HCM",
     "Tòa nhà Phú Mỹ Hưng, số 8 Hoàng Văn Thái, Quận 7, TP. Hồ Chí Minh", "FULL_TIME", "FROM_3_TO_5", 30, 45, 2, 35,
     ["Figma", "UI/UX"],
     ["Thiết kế trải nghiệm cho các tính năng trên ứng dụng MoMo", "Nghiên cứu người dùng và kiểm thử khả dụng",
      "Xây dựng và duy trì hệ thống thiết kế (design system)"],
     ["Tối thiểu 3 năm kinh nghiệm thiết kế sản phẩm số", "Thành thạo Figma, có portfolio", "Tư duy lấy người dùng làm trung tâm"]),
    ("momo", "Chuyên viên Chăm sóc Khách hàng", "cham-soc-khach-hang", "HCM",
     "Tòa nhà Phú Mỹ Hưng, số 8 Hoàng Văn Thái, Quận 7, TP. Hồ Chí Minh", "FULL_TIME", "NONE", 8, 12, 15, 20,
     ["Giao tiếp", "Tin học văn phòng", "Giải quyết vấn đề"],
     ["Hỗ trợ người dùng qua tổng đài, chat và email", "Tiếp nhận và xử lý khiếu nại giao dịch",
      "Ghi nhận phản hồi để cải thiện sản phẩm"],
     ["Tốt nghiệp cao đẳng trở lên", "Giọng nói rõ ràng, kiên nhẫn", "Có thể làm việc theo ca, kể cả cuối tuần"]),
    ("momo", "Chuyên viên Tuân thủ (Compliance)", "phap-ly-luat", "HCM",
     "Tòa nhà Phú Mỹ Hưng, số 8 Hoàng Văn Thái, Quận 7, TP. Hồ Chí Minh", "FULL_TIME", "FROM_3_TO_5", 25, 40, 1, 40,
     ["Giải quyết vấn đề", "Tiếng Anh"],
     ["Theo dõi việc tuân thủ quy định về trung gian thanh toán", "Xây dựng quy trình phòng chống rửa tiền (AML)",
      "Làm việc với cơ quan quản lý khi có yêu cầu"],
     ["Tốt nghiệp Luật, Tài chính hoặc Ngân hàng", "Tối thiểu 3 năm kinh nghiệm tuân thủ trong lĩnh vực tài chính",
      "Tiếng Anh tốt"]),
    ("momo", "Biên tập viên Video ngắn (Freelance)", "thiet-ke-sang-tao", "HCM",
     "Làm việc từ xa, họp định kỳ tại văn phòng Quận 7, TP. Hồ Chí Minh", "FREELANCE", "UNDER_1", 8, 15, 3, 25,
     ["Dựng video", "Photoshop", "Viết nội dung (Copywriting)"],
     ["Dựng video ngắn cho TikTok, Facebook Reels, YouTube Shorts", "Lên ý tưởng nội dung theo chiến dịch",
      "Bàn giao sản phẩm theo lịch đã thống nhất"],
     ["Có sản phẩm dựng video đã thực hiện", "Sử dụng thành thạo Premiere hoặc CapCut", "Chủ động thời gian, đúng hạn"]),
    # ---------- Tiki ----------
    ("tiki", "Chuyên viên Vận hành Nhà bán hàng", "thuong-mai-dien-tu", "HCM",
     "52 Út Tịch, phường 4, Tân Bình, TP. Hồ Chí Minh", "FULL_TIME", "FROM_1_TO_3", 12, 18, 4, 30,
     ["Excel", "Giao tiếp", "Quản lý khách hàng (CRM)"],
     ["Hỗ trợ nhà bán hàng đăng sản phẩm và vận hành gian hàng", "Theo dõi chỉ số đơn hàng, tỷ lệ hủy, đánh giá",
      "Phối hợp với kho vận để xử lý sự cố đơn hàng"],
     ["Tối thiểu 1 năm kinh nghiệm thương mại điện tử", "Thành thạo Excel", "Cẩn thận, chủ động"]),
    ("tiki", "Nhân viên Kho (bán thời gian)", "logistics-van-tai", "HCM",
     "Kho Tiki, TP. Hồ Chí Minh", "PART_TIME", "NONE", 7, 10, 30, 15,
     ["Quản lý kho", "Làm việc nhóm"],
     ["Nhận hàng, kiểm đếm và sắp xếp hàng hóa", "Lấy hàng, đóng gói theo đơn", "Ca làm linh hoạt 4–6 tiếng"],
     ["Sức khỏe tốt", "Không yêu cầu kinh nghiệm", "Phù hợp sinh viên muốn làm thêm"]),
    ("tiki", "Chuyên viên SEO và Content", "marketing-truyen-thong", "HCM",
     "52 Út Tịch, phường 4, Tân Bình, TP. Hồ Chí Minh", "FULL_TIME", "FROM_1_TO_3", 13, 20, 2, 35,
     ["SEO", "Content Marketing", "Viết nội dung (Copywriting)"],
     ["Nghiên cứu từ khóa và tối ưu trang danh mục sản phẩm", "Viết và biên tập nội dung chuẩn SEO",
      "Theo dõi thứ hạng và lưu lượng truy cập"],
     ["Tối thiểu 1 năm kinh nghiệm SEO", "Viết tiếng Việt tốt", "Biết sử dụng Google Search Console, Google Analytics"]),
    ("tiki", "Thực tập sinh Phân tích Nghiệp vụ (BA)", "thuong-mai-dien-tu", "HCM",
     "52 Út Tịch, phường 4, Tân Bình, TP. Hồ Chí Minh", "INTERNSHIP", "NONE", 4, 6, 3, 25,
     ["Phân tích nghiệp vụ (BA)", "SQL", "Excel"],
     ["Thu thập yêu cầu và viết tài liệu đặc tả tính năng", "Vẽ quy trình nghiệp vụ, wireframe đơn giản",
      "Tham gia kiểm thử chấp nhận cùng đội sản phẩm"],
     ["Sinh viên năm 3, năm 4 các ngành CNTT, Kinh tế", "Tư duy logic tốt", "Làm việc tối thiểu 4 ngày/tuần"]),
    # ---------- GHN ----------
    ("ghn", "Nhân viên Giao hàng (Đối tác tự do)", "logistics-van-tai", "HN",
     "Các bưu cục GHN tại Hà Nội", "FREELANCE", "NONE", 10, 18, 50, 20,
     ["Giao tiếp", "Quản lý thời gian"],
     ["Nhận hàng tại bưu cục và giao đến khách hàng", "Thu tiền hộ (COD) và đối soát cuối ngày",
      "Tự chọn khung giờ và khu vực giao hàng"],
     ["Có xe máy và điện thoại thông minh", "Thông thạo đường khu vực đăng ký", "Trung thực, chăm chỉ"]),
    ("ghn", "Trưởng Bưu cục", "logistics-van-tai", "DN",
     "Bưu cục GHN Đà Nẵng, TP. Đà Nẵng", "FULL_TIME", "FROM_3_TO_5", 15, 22, 2, 30,
     ["Lãnh đạo nhóm", "Quản lý kho", "Excel"],
     ["Quản lý hoạt động nhận, phân loại và giao hàng tại bưu cục", "Điều phối đội ngũ giao hàng, đảm bảo chỉ tiêu",
      "Báo cáo sản lượng và chất lượng dịch vụ"],
     ["Tối thiểu 3 năm kinh nghiệm vận hành, trong đó 1 năm quản lý", "Kỹ năng lãnh đạo và giải quyết vấn đề",
      "Thành thạo Excel"]),
    ("ghn", "Nhân viên Tổng đài Chăm sóc Khách hàng", "cham-soc-khach-hang", "HCM",
     "405/15 Xô Viết Nghệ Tĩnh, Bình Thạnh, TP. Hồ Chí Minh", "PART_TIME", "NONE", 6, 9, 10, 15,
     ["Giao tiếp", "Tin học văn phòng"],
     ["Trả lời cuộc gọi về tình trạng đơn hàng", "Hỗ trợ khách hàng và nhà bán hàng xử lý sự cố giao nhận",
      "Ca làm 4 tiếng, xoay ca linh hoạt"],
     ["Giọng nói dễ nghe, không nói ngọng", "Biết sử dụng máy tính cơ bản", "Ưu tiên sinh viên"]),
    ("ghn", "Lập trình viên Mobile (Android/iOS)", "cong-nghe-thong-tin", "HCM",
     "405/15 Xô Viết Nghệ Tĩnh, Bình Thạnh, TP. Hồ Chí Minh", "FULL_TIME", "FROM_1_TO_3", 20, 35, 2, 30,
     ["Android", "iOS", "Git"],
     ["Phát triển ứng dụng cho tài xế và khách hàng của GHN", "Tối ưu hiệu năng và trải nghiệm trên thiết bị cấu hình thấp",
      "Phối hợp với backend tích hợp API"],
     ["Tối thiểu 1 năm kinh nghiệm phát triển mobile", "Thành thạo Kotlin hoặc Swift, ưu tiên biết Flutter",
      "Đã có ứng dụng phát hành trên Store là lợi thế"]),
    # ---------- Vietnam Airlines ----------
    ("vietnamairlines", "Tiếp viên Hàng không", "du-lich-nha-hang-khach-san", "HN",
     "200 Nguyễn Sơn, Bồ Đề, Long Biên, Hà Nội", "FULL_TIME", "NONE", 15, 25, 40, 45,
     ["Tiếng Anh", "Giao tiếp", "Làm việc nhóm"],
     ["Phục vụ hành khách trên các chuyến bay nội địa và quốc tế", "Đảm bảo an toàn chuyến bay theo quy trình",
      "Tham gia khóa huấn luyện tiếp viên trước khi bay"],
     ["Tốt nghiệp THPT trở lên, tuổi từ 18 đến 27", "Chiều cao và sức khỏe theo tiêu chuẩn tiếp viên",
      "Tiếng Anh TOEIC 550 trở lên"]),
    ("vietnamairlines", "Nhân viên Phục vụ Hành khách Mặt đất", "du-lich-nha-hang-khach-san", "KH",
     "Sân bay Quốc tế Cam Ranh, tỉnh Khánh Hòa", "CONTRACT", "UNDER_1", 9, 13, 8, 30,
     ["Tiếng Anh", "Giao tiếp"],
     ["Làm thủ tục check-in, ký gửi hành lý cho hành khách", "Hướng dẫn hành khách tại khu vực sân bay",
      "Hỗ trợ hành khách đặc biệt (người cao tuổi, trẻ em đi một mình)"],
     ["Tốt nghiệp cao đẳng trở lên", "Tiếng Anh giao tiếp tốt", "Làm việc theo ca, hợp đồng 12 tháng"]),
    ("vietnamairlines", "Kỹ sư Bảo dưỡng Tàu bay", "dien-dien-tu-co-khi", "HCM",
     "Sân bay Tân Sơn Nhất, TP. Hồ Chí Minh", "FULL_TIME", "OVER_5", 35, 60, 3, 40,
     ["Tiếng Anh", "Giải quyết vấn đề", "Làm việc nhóm"],
     ["Thực hiện bảo dưỡng định kỳ và khắc phục hỏng hóc tàu bay", "Kiểm tra, ký xác nhận tàu bay đủ điều kiện bay",
      "Hướng dẫn kỹ thuật viên mới"],
     ["Tốt nghiệp Kỹ thuật Hàng không, Cơ khí hoặc Điện tử", "Tối thiểu 5 năm kinh nghiệm bảo dưỡng tàu bay",
      "Có chứng chỉ B1/B2 là lợi thế"]),
    ("vietnamairlines", "Giảng viên Đào tạo Dịch vụ Khách hàng", "giao-duc-dao-tao", "HN",
     "Trung tâm Huấn luyện, 200 Nguyễn Sơn, Long Biên, Hà Nội", "CONTRACT", "FROM_3_TO_5", 18, 28, 2, 35,
     ["Giảng dạy", "Thuyết trình", "Tiếng Anh"],
     ["Giảng dạy kỹ năng phục vụ hành khách cho nhân viên mới", "Biên soạn và cập nhật giáo trình",
      "Đánh giá kết quả học viên sau khóa học"],
     ["Tối thiểu 3 năm kinh nghiệm dịch vụ khách hàng ngành hàng không hoặc khách sạn", "Kỹ năng thuyết trình tốt",
      "Tiếng Anh thành thạo"]),
    ("vietnamairlines", "Nhân viên An ninh Hàng không", "khac", "QN",
     "Cảng hàng không Quốc tế Vân Đồn, tỉnh Quảng Ninh", "FULL_TIME", "UNDER_1", 9, 14, 6, 30,
     ["Làm việc nhóm", "Giao tiếp"],
     ["Kiểm tra an ninh hành khách, hành lý trước chuyến bay", "Tuần tra, giám sát khu vực hạn chế",
      "Xử lý tình huống theo quy trình an ninh hàng không"],
     ["Nam/nữ tuổi từ 20 đến 30, sức khỏe tốt", "Tốt nghiệp trung cấp trở lên", "Được đào tạo cấp chứng chỉ nghiệp vụ"]),
    # ---------- FPT Long Châu ----------
    ("longchau", "Dược sĩ Bán hàng", "y-te-duoc-pham", "HCM",
     "Nhà thuốc FPT Long Châu, các quận tại TP. Hồ Chí Minh", "FULL_TIME", "NONE", 9, 15, 30, 20,
     ["Giao tiếp", "Tin học văn phòng"],
     ["Tư vấn và bán thuốc theo đơn, không theo đơn", "Sắp xếp, bảo quản thuốc theo tiêu chuẩn GPP",
      "Chăm sóc khách hàng thân thiết"],
     ["Tốt nghiệp Trung cấp Dược trở lên", "Chấp nhận mới ra trường, được đào tạo", "Thân thiện, tận tâm"]),
    ("longchau", "Dược sĩ Quản lý Nhà thuốc", "y-te-duoc-pham", "LD",
     "Nhà thuốc FPT Long Châu, TP. Đà Lạt, tỉnh Lâm Đồng", "FULL_TIME", "FROM_1_TO_3", 14, 22, 2, 30,
     ["Lãnh đạo nhóm", "Giao tiếp", "Excel"],
     ["Quản lý vận hành và doanh số nhà thuốc", "Đào tạo, phân ca cho dược sĩ bán hàng",
      "Đảm bảo nhà thuốc tuân thủ quy định chuyên môn"],
     ["Tốt nghiệp Cao đẳng Dược trở lên, có chứng chỉ hành nghề", "Tối thiểu 1 năm kinh nghiệm tại nhà thuốc",
      "Kỹ năng quản lý đội nhóm"]),
    ("longchau", "Điều dưỡng Trung tâm Tiêm chủng", "y-te-duoc-pham", "HN",
     "Trung tâm Tiêm chủng Long Châu, Hà Nội", "FULL_TIME", "UNDER_1", 10, 15, 10, 25,
     ["Giao tiếp", "Làm việc nhóm"],
     ["Thực hiện tiêm chủng theo đúng quy trình an toàn", "Theo dõi phản ứng sau tiêm và hướng dẫn khách hàng",
      "Quản lý hồ sơ tiêm chủng"],
     ["Tốt nghiệp Cao đẳng Điều dưỡng trở lên, có chứng chỉ hành nghề", "Có chứng nhận tiêm chủng an toàn là lợi thế",
      "Cẩn thận, nhẹ nhàng với trẻ em"]),
    ("longchau", "Nhân viên Bán hàng (bán thời gian)", "kinh-doanh-ban-hang", "DNA",
     "Nhà thuốc FPT Long Châu, TP. Biên Hòa, tỉnh Đồng Nai", "PART_TIME", "NONE", 5, 8, 8, 15,
     ["Giao tiếp", "Làm việc nhóm"],
     ["Hỗ trợ trưng bày sản phẩm và thanh toán", "Giới thiệu chương trình khuyến mãi tới khách hàng",
      "Ca làm 4–5 tiếng, phù hợp sinh viên"],
     ["Không yêu cầu kinh nghiệm", "Ưu tiên sinh viên ngành Y Dược", "Nhanh nhẹn, vui vẻ"]),
    # ---------- Coteccons ----------
    ("coteccons", "Kỹ sư Giám sát Thi công", "xay-dung-kien-truc", "HCM",
     "236/6 Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh (làm việc tại công trường)", "FULL_TIME", "FROM_3_TO_5", 20, 30, 5, 30,
     ["AutoCAD", "Quản lý dự án", "Làm việc nhóm"],
     ["Giám sát tiến độ, chất lượng và an toàn thi công", "Nghiệm thu khối lượng với chủ đầu tư và tư vấn giám sát",
      "Phối hợp với nhà thầu phụ xử lý vướng mắc tại công trường"],
     ["Tốt nghiệp Kỹ sư Xây dựng", "Tối thiểu 3 năm kinh nghiệm giám sát nhà cao tầng", "Sẵn sàng làm việc tại công trường"]),
    ("coteccons", "Kỹ sư Dự toán (QS)", "xay-dung-kien-truc", "HN",
     "Văn phòng Coteccons tại Hà Nội", "FULL_TIME", "FROM_1_TO_3", 15, 25, 3, 35,
     ["AutoCAD", "Excel"],
     ["Bóc tách khối lượng và lập dự toán công trình", "Lập hồ sơ thanh toán, quyết toán với chủ đầu tư",
      "Kiểm soát chi phí trong quá trình thi công"],
     ["Tốt nghiệp Kỹ sư Xây dựng hoặc Kinh tế Xây dựng", "Tối thiểu 1 năm kinh nghiệm QS", "Thành thạo AutoCAD và Excel"]),
    ("coteccons", "Chuyên viên Phát triển Kinh doanh Dự án Bất động sản", "bat-dong-san", "HCM",
     "236/6 Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh", "FULL_TIME", "FROM_3_TO_5", 25, 40, 2, 40,
     ["Đàm phán", "Thuyết trình", "Bán hàng B2B"],
     ["Tìm kiếm và tiếp cận các chủ đầu tư dự án bất động sản", "Chuẩn bị hồ sơ năng lực và tham gia đấu thầu",
      "Duy trì quan hệ với khách hàng sau khi trúng thầu"],
     ["Tối thiểu 3 năm kinh nghiệm phát triển kinh doanh trong ngành xây dựng hoặc bất động sản",
      "Kỹ năng đàm phán và thuyết trình tốt", "Có mạng lưới quan hệ với chủ đầu tư là lợi thế"]),
    ("coteccons", "Kiến trúc sư Thiết kế (Design & Build)", "xay-dung-kien-truc", "HY",
     "Dự án khu công nghiệp tại tỉnh Hưng Yên", "CONTRACT", "FROM_1_TO_3", 18, 28, 2, 30,
     ["AutoCAD", "Photoshop", "Làm việc nhóm"],
     ["Thiết kế kiến trúc nhà xưởng và công trình công nghiệp", "Triển khai hồ sơ thiết kế kỹ thuật và bản vẽ thi công",
      "Phối hợp với đội kết cấu, cơ điện"],
     ["Tốt nghiệp Kiến trúc sư", "Tối thiểu 1 năm kinh nghiệm thiết kế", "Hợp đồng theo dự án 18 tháng"]),
]


def run() -> None:
    db = SessionLocal()
    try:
        admin = (db.query(User).join(Role, Role.id == User.role_id).filter(Role.name == "ADMIN")
                 .order_by(User.id).first())
        if admin is None:
            raise SystemExit("Chưa có tài khoản Admin, hãy đặt ADMIN_EMAIL/ADMIN_PASSWORD và chạy python -m src.seeds.run")
        industries = {slug: id_ for id_, slug in db.query(Industry.id, Industry.slug)}
        provinces = {code: id_ for id_, code in db.query(Province.id, Province.code)}
        skills = {name: id_ for id_, name in db.query(Skill.id, Skill.name)}
        created = skipped = 0
        for (key, title, industry, province, address, employment, experience, sal_min, sal_max,
             positions, days, skill_names, description, requirements) in JOBS:
            user = db.query(User).filter(User.email == f"tuyendung.{key}@vieco.click").first()
            if user is None:
                raise SystemExit(f"Chưa có tài khoản tuyendung.{key}@vieco.click, hãy chạy python -m src.seeds.demo_companies")
            company = (db.query(Company).join(CompanyMember, CompanyMember.company_id == Company.id)
                       .filter(CompanyMember.user_id == user.id).one())
            if db.query(Job.id).filter(Job.company_id == company.id, Job.title == title).first():
                skipped += 1
                continue
            job = job_service.create_job(db, user, JobCreate(
                title=title, industry_id=industries[industry], province_id=provinces[province], work_address=address,
                description="\n".join(description), requirements="\n".join(requirements),
                benefits="\n".join(BENEFITS[key]),
                salary_min=sal_min * M if sal_min is not None else None,
                salary_max=sal_max * M if sal_max is not None else None,
                experience_level=experience, employment_type=employment, positions=positions,
                deadline=date.today() + timedelta(days=days), skill_ids=[skills[s] for s in skill_names],
                action="submit"))
            job_service.approve_job(db, admin, job.id)
            print(f"Đã đăng: {company.name} — {title}")
            created += 1
        print(f"Xong: đăng mới {created} tin, bỏ qua {skipped} tin đã có.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
