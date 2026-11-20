"""Tạo 10 tài khoản nhà tuyển dụng và 10 hồ sơ công ty mẫu (trạng thái Chờ duyệt) để demo.

Chạy từ thư mục server/:  python -m src.seeds.demo_companies

- Đi qua đúng validation và nghiệp vụ của API: RegisterRequest/register_user, CompanyCreate/create_company.
- Idempotent: email đã tồn tại thì bỏ qua, không ghi đè.
- Hình ảnh (logo, ảnh bìa, ảnh không gian làm việc) để trống, nhà tuyển dụng tự tải lên sau.
- Thông tin công ty tổng hợp từ nguồn công khai, chỉ dùng cho dữ liệu demo.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from src.config.database import SessionLocal
from src.models import Industry, Province, User
from src.schemas.auth import RegisterRequest
from src.schemas.company import CompanyCreate
from src.services import auth_service, company_service

DEMO_PASSWORD = os.getenv("DEMO_EMPLOYER_PASSWORD", "123345678A")

# (email, người phụ trách, tên công ty, slug ngành, mã tỉnh, quy mô, website, địa chỉ, giới thiệu)
COMPANIES = [
    (
        "tuyendung.fpt@vieco.click", "Bộ phận Tuyển dụng FPT",
        "Tập đoàn FPT", "cong-nghe-thong-tin", "HN", "1000+", "https://fpt.com",
        "Tòa nhà FPT, số 10 Phạm Văn Bạch, phường Dịch Vọng, quận Cầu Giấy, Hà Nội",
        "Tập đoàn FPT được thành lập năm 1988, là một trong những tập đoàn công nghệ hàng đầu Việt Nam "
        "với ba lĩnh vực cốt lõi: Công nghệ, Viễn thông và Giáo dục.\n\n"
        "FPT cung cấp dịch vụ chuyển đổi số, phát triển phần mềm, trí tuệ nhân tạo, điện toán đám mây "
        "và tích hợp hệ thống cho khách hàng tại Việt Nam và nhiều quốc gia trên thế giới.\n\n"
        "Môi trường làm việc năng động, đề cao tinh thần đổi mới sáng tạo, có lộ trình phát triển nghề nghiệp rõ ràng, "
        "chương trình đào tạo nội bộ và cơ hội tham gia các dự án quốc tế.",
    ),
    (
        "tuyendung.viettel@vieco.click", "Bộ phận Tuyển dụng Viettel",
        "Tập đoàn Công nghiệp – Viễn thông Quân đội (Viettel)", "cong-nghe-thong-tin", "HN", "1000+",
        "https://viettel.com.vn",
        "Lô D26, Khu đô thị mới Cầu Giấy, phố Tôn Thất Thuyết, phường Yên Hòa, quận Cầu Giấy, Hà Nội",
        "Viettel được thành lập năm 1989, là tập đoàn công nghiệp – viễn thông hàng đầu Việt Nam, "
        "hoạt động trong các lĩnh vực viễn thông, công nghệ thông tin, nghiên cứu sản xuất thiết bị công nghệ cao, "
        "chuyển đổi số và dịch vụ số.\n\n"
        "Viettel đã đầu tư kinh doanh viễn thông tại nhiều thị trường ở châu Á, châu Phi và châu Mỹ.\n\n"
        "Viettel tìm kiếm những nhân sự có tinh thần trách nhiệm, đam mê công nghệ và mong muốn tham gia "
        "các dự án quy mô lớn có tác động tới hàng triệu người dùng.",
    ),
    (
        "tuyendung.vinamilk@vieco.click", "Bộ phận Tuyển dụng Vinamilk",
        "Công ty Cổ phần Sữa Việt Nam (Vinamilk)", "nong-nghiep-thuc-pham", "HCM", "1000+",
        "https://www.vinamilk.com.vn",
        "Số 10 Tân Trào, phường Tân Phú, Quận 7, TP. Hồ Chí Minh",
        "Vinamilk được thành lập năm 1976, là doanh nghiệp sản xuất sữa và các sản phẩm từ sữa hàng đầu Việt Nam.\n\n"
        "Vinamilk sở hữu hệ thống nhà máy, trang trại bò sữa và mạng lưới phân phối trải rộng trên cả nước, "
        "sản phẩm được xuất khẩu tới nhiều quốc gia và vùng lãnh thổ.\n\n"
        "Công ty mang đến môi trường làm việc chuyên nghiệp, chú trọng đào tạo và phát triển đội ngũ, "
        "với cơ hội việc làm trong các mảng sản xuất, chất lượng, chuỗi cung ứng, kinh doanh và marketing.",
    ),
    (
        "tuyendung.vietcombank@vieco.click", "Bộ phận Tuyển dụng Vietcombank",
        "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)", "tai-chinh-ngan-hang", "HN", "1000+",
        "https://www.vietcombank.com.vn",
        "198 Trần Quang Khải, phường Lý Thái Tổ, quận Hoàn Kiếm, Hà Nội",
        "Vietcombank được thành lập năm 1963, là một trong những ngân hàng thương mại lớn nhất Việt Nam.\n\n"
        "Ngân hàng cung cấp đầy đủ các dịch vụ tài chính cho khách hàng cá nhân và doanh nghiệp: tiền gửi, tín dụng, "
        "thanh toán quốc tế, kinh doanh ngoại tệ, thẻ và ngân hàng số, với mạng lưới chi nhánh trên toàn quốc.\n\n"
        "Vietcombank chú trọng xây dựng đội ngũ nhân sự chuyên nghiệp, có chương trình đào tạo bài bản "
        "và lộ trình thăng tiến rõ ràng.",
    ),
    (
        "tuyendung.momo@vieco.click", "Bộ phận Tuyển dụng MoMo",
        "Công ty Cổ phần Dịch vụ Di động Trực tuyến (MoMo)", "tai-chinh-ngan-hang", "HCM", "1000+",
        "https://momo.vn",
        "Tòa nhà Phú Mỹ Hưng, số 8 Hoàng Văn Thái, phường Tân Phú, Quận 7, TP. Hồ Chí Minh",
        "MoMo là siêu ứng dụng thanh toán và tài chính số phổ biến tại Việt Nam, cho phép người dùng chuyển tiền, "
        "thanh toán hóa đơn, mua sắm và sử dụng nhiều dịch vụ tài chính ngay trên điện thoại.\n\n"
        "Đội ngũ MoMo làm việc với các công nghệ hiện đại về dữ liệu, bảo mật và hệ thống chịu tải lớn, "
        "phục vụ hàng chục triệu người dùng.\n\n"
        "Môi trường làm việc trẻ trung, đề cao tinh thần chủ động và học hỏi, khuyến khích nhân viên đề xuất ý tưởng mới.",
    ),
    (
        "tuyendung.tiki@vieco.click", "Bộ phận Tuyển dụng Tiki",
        "Công ty Cổ phần Tiki", "thuong-mai-dien-tu", "HCM", "1000+", "https://tiki.vn",
        "52 Út Tịch, phường 4, quận Tân Bình, TP. Hồ Chí Minh",
        "Tiki được thành lập năm 2010, là một trong những sàn thương mại điện tử hàng đầu Việt Nam, "
        "nổi bật với dịch vụ giao hàng nhanh và cam kết hàng chính hãng.\n\n"
        "Tiki vận hành nền tảng mua sắm trực tuyến cùng hệ thống kho vận và giao nhận riêng, "
        "kết nối hàng nghìn nhà bán hàng với khách hàng trên cả nước.\n\n"
        "Tiki tìm kiếm những nhân sự yêu thích công nghệ và thương mại, mong muốn xây dựng trải nghiệm mua sắm tốt hơn "
        "cho người Việt.",
    ),
    (
        "tuyendung.ghn@vieco.click", "Bộ phận Tuyển dụng GHN",
        "Công ty Cổ phần Dịch vụ Giao Hàng Nhanh (GHN)", "logistics-van-tai", "HCM", "1000+", "https://ghn.vn",
        "405/15 Xô Viết Nghệ Tĩnh, phường 24, quận Bình Thạnh, TP. Hồ Chí Minh",
        "Giao Hàng Nhanh (GHN) được thành lập năm 2012, là doanh nghiệp giao nhận chuyên phục vụ thương mại điện tử "
        "tại Việt Nam.\n\n"
        "GHN vận hành mạng lưới bưu cục, kho phân loại và đội ngũ giao hàng phủ khắp các tỉnh thành, "
        "ứng dụng công nghệ để tối ưu tuyến đường và theo dõi đơn hàng theo thời gian thực.\n\n"
        "Công ty tuyển dụng thường xuyên các vị trí vận hành, kho vận, công nghệ và chăm sóc khách hàng, "
        "với môi trường làm việc năng động và cơ hội thăng tiến cho người chăm chỉ.",
    ),
    (
        "tuyendung.vietnamairlines@vieco.click", "Bộ phận Tuyển dụng Vietnam Airlines",
        "Tổng Công ty Hàng không Việt Nam (Vietnam Airlines)", "du-lich-nha-hang-khach-san", "HN", "1000+",
        "https://www.vietnamairlines.com",
        "200 Nguyễn Sơn, phường Bồ Đề, quận Long Biên, Hà Nội",
        "Vietnam Airlines là hãng hàng không quốc gia của Việt Nam, khai thác mạng đường bay nội địa và quốc tế "
        "kết nối Việt Nam với nhiều điểm đến tại châu Á, châu Âu và châu Úc.\n\n"
        "Hãng là thành viên của liên minh hàng không SkyTeam, hướng tới chất lượng dịch vụ tiêu chuẩn quốc tế.\n\n"
        "Vietnam Airlines tuyển dụng các vị trí tiếp viên, phi công, kỹ thuật bảo dưỡng tàu bay, dịch vụ mặt đất "
        "và khối văn phòng, với chương trình đào tạo chuyên sâu theo tiêu chuẩn ngành hàng không.",
    ),
    (
        "tuyendung.longchau@vieco.click", "Bộ phận Tuyển dụng FPT Long Châu",
        "Hệ thống Nhà thuốc FPT Long Châu", "y-te-duoc-pham", "HCM", "1000+",
        "https://nhathuoclongchau.com.vn",
        "379–381 Hai Bà Trưng, phường 8, Quận 3, TP. Hồ Chí Minh",
        "FPT Long Châu là chuỗi nhà thuốc bán lẻ thuộc Công ty Cổ phần Bán lẻ Kỹ thuật số FPT (FPT Retail), "
        "với hệ thống nhà thuốc và trung tâm tiêm chủng trên khắp cả nước.\n\n"
        "Long Châu cung cấp thuốc, thực phẩm chức năng, dược mỹ phẩm và thiết bị y tế chính hãng, "
        "cùng đội ngũ dược sĩ tư vấn tận tâm.\n\n"
        "Công ty thường xuyên tuyển dụng dược sĩ, nhân viên tư vấn và nhân sự vận hành chuỗi, "
        "có chương trình đào tạo chuyên môn và lộ trình phát triển lên quản lý nhà thuốc.",
    ),
    (
        "tuyendung.coteccons@vieco.click", "Bộ phận Tuyển dụng Coteccons",
        "Công ty Cổ phần Xây dựng Coteccons", "xay-dung-kien-truc", "HCM", "1000+", "https://www.coteccons.vn",
        "236/6 Điện Biên Phủ, phường 17, quận Bình Thạnh, TP. Hồ Chí Minh",
        "Coteccons là một trong những tổng thầu xây dựng hàng đầu Việt Nam, thực hiện các dự án nhà cao tầng, "
        "khu nghỉ dưỡng, nhà máy công nghiệp và công trình hạ tầng.\n\n"
        "Công ty cung cấp dịch vụ tổng thầu thiết kế và thi công (Design & Build), quản lý dự án "
        "và thi công cơ điện với các tiêu chuẩn an toàn lao động nghiêm ngặt.\n\n"
        "Coteccons tìm kiếm kỹ sư xây dựng, kỹ sư cơ điện, chỉ huy trưởng công trình và nhân sự quản lý dự án "
        "mong muốn phát triển sự nghiệp tại các công trình quy mô lớn.",
    ),
]


def run() -> None:
    db = SessionLocal()
    try:
        industries = {slug: id_ for id_, slug in db.query(Industry.id, Industry.slug)}
        provinces = {code: id_ for id_, code in db.query(Province.id, Province.code)}
        created = skipped = 0
        for email, contact, name, industry, province, size, website, address, description in COMPANIES:
            if db.query(User.id).filter(User.email == email).first():
                print(f"Bỏ qua (email đã có): {email}")
                skipped += 1
                continue
            auth_service.register_user(db, RegisterRequest(
                email=email, password=DEMO_PASSWORD, full_name=contact, role="EMPLOYER"))
            user = db.query(User).filter(User.email == email).one()
            company_service.create_company(db, user, CompanyCreate(
                name=name, description=description, industry_id=industries[industry], size=size,
                website=website, address=address, province_id=provinces[province]))
            print(f"Đã tạo: {email}  →  {name} (Chờ duyệt)")
            created += 1
        print(f"Xong: tạo mới {created}, bỏ qua {skipped}.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
