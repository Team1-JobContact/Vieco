/* Điều khoản sử dụng khi đăng ký: bấm "Điều khoản sử dụng" để mở hộp thoại đọc toàn văn.
   Nút "Tôi đã đọc và đồng ý" chỉ bật khi đã cuộn tới cuối; đồng ý xong ô tick được chọn sẵn.
   Người dùng tick ô đồng ý khi chưa mở điều khoản thì hộp thoại tự mở ra để đọc trước. */
(function () {
    "use strict";
    var V = window.Vieco;
    var checkbox = document.querySelector('#register-form [name="accept_terms"]');
    if (!V || !checkbox) return;
    var h = V.h;
    var hasRead = false;

    var EFFECTIVE_DATE = "24/11/2026";
    var TERMS = [
        ["1. Giới thiệu và chấp thuận", [
            "Vieco là nền tảng trực tuyến kết nối ứng viên với doanh nghiệp tuyển dụng, cung cấp các dịch vụ tìm việc, tạo CV, ứng tuyển, đăng tin tuyển dụng và trợ lý AI.",
            "Khi đăng ký tài khoản hoặc sử dụng Vieco, bạn xác nhận đã đọc, hiểu và đồng ý tuân thủ toàn bộ Điều khoản sử dụng này. Nếu không đồng ý, vui lòng không sử dụng dịch vụ."
        ]],
        ["2. Tài khoản người dùng", [
            "Bạn phải từ đủ 15 tuổi trở lên và cung cấp thông tin chính xác, đầy đủ, cập nhật khi đăng ký.",
            "Mỗi người chỉ đăng ký một vai trò cho một tài khoản: Ứng viên hoặc Nhà tuyển dụng.",
            "Bạn tự chịu trách nhiệm bảo mật mật khẩu và mọi hoạt động diễn ra dưới tài khoản của mình. Hãy báo ngay cho Vieco nếu phát hiện tài khoản bị sử dụng trái phép.",
            "Không được mua bán, cho thuê, chuyển nhượng tài khoản hoặc mạo danh người, tổ chức khác."
        ]],
        ["3. Quy định dành cho ứng viên", [
            "Thông tin trong hồ sơ và CV phải trung thực, đúng với học vấn, kinh nghiệm và kỹ năng thực tế của bạn.",
            "Khi ứng tuyển, bạn đồng ý cho nhà tuyển dụng của tin đó xem hồ sơ, CV và thư giới thiệu bạn đã gửi.",
            "Không gửi hồ sơ hàng loạt mang tính spam hoặc dùng thông tin, CV của người khác."
        ]],
        ["4. Quy định dành cho nhà tuyển dụng", [
            "Doanh nghiệp phải cung cấp thông tin công ty thật và chỉ được đăng tin sau khi hồ sơ công ty được Vieco duyệt.",
            "Tin tuyển dụng phải mô tả đúng vị trí, mức lương, quyền lợi và điều kiện làm việc thực tế.",
            "Nghiêm cấm thu phí ứng viên dưới mọi hình thức (đặt cọc, phí hồ sơ, phí đào tạo…), đăng tin đa cấp, tin lừa đảo hoặc tuyển dụng cho công việc vi phạm pháp luật.",
            "Không đưa ra yêu cầu phân biệt đối xử về giới tính, tuổi tác, dân tộc, tôn giáo, ngoại hình, tình trạng hôn nhân trái với quy định của pháp luật lao động.",
            "Thông tin cá nhân của ứng viên chỉ được dùng cho mục đích tuyển dụng của chính tin đó; không chia sẻ, mua bán hay dùng cho mục đích khác."
        ]],
        ["5. Nội dung bị cấm", [
            "Nội dung vi phạm pháp luật Việt Nam, xâm phạm an ninh quốc gia, trật tự an toàn xã hội.",
            "Nội dung khiêu dâm, bạo lực, xúc phạm danh dự, nhân phẩm của người khác.",
            "Thông tin sai sự thật, quảng cáo trá hình, đường dẫn độc hại hoặc tệp chứa mã độc.",
            "Nội dung xâm phạm quyền sở hữu trí tuệ, bí mật kinh doanh hoặc quyền riêng tư của bên thứ ba."
        ]],
        ["6. Tính năng trí tuệ nhân tạo (AI)", [
            "Vieco cung cấp các tính năng AI như trợ lý trò chuyện, tạo CV, phân tích mức độ phù hợp, tối ưu CV và viết tin tuyển dụng. Nội dung bạn nhập vào các tính năng này được gửi tới nhà cung cấp dịch vụ AI (Anthropic) để xử lý.",
            "Kết quả do AI tạo ra chỉ mang tính tham khảo và có thể chưa chính xác. Bạn có trách nhiệm đọc lại, chỉnh sửa cho đúng sự thật trước khi lưu, gửi hoặc đăng.",
            "Không nhập vào tính năng AI các thông tin nhạy cảm như mật khẩu, số căn cước công dân, số tài khoản ngân hàng.",
            "Vieco có thể giới hạn số lượt sử dụng AI để bảo đảm chất lượng dịch vụ."
        ]],
        ["7. Dữ liệu cá nhân", [
            "Vieco thu thập các thông tin bạn cung cấp (họ tên, email, số điện thoại, hồ sơ, CV, ảnh) để vận hành dịch vụ: hiển thị hồ sơ, xử lý ứng tuyển, gửi thông báo và email liên quan.",
            "Mật khẩu được mã hóa một chiều; Vieco không lưu và không thể xem mật khẩu gốc của bạn.",
            "Bạn có thể chọn chế độ hiển thị hồ sơ Riêng tư, cập nhật hoặc xóa thông tin, CV của mình bất cứ lúc nào. CV đã dùng để ứng tuyển được giữ lại để nhà tuyển dụng tra cứu đơn đã nhận.",
            "Vieco không bán dữ liệu cá nhân của bạn cho bên thứ ba và chỉ cung cấp khi có yêu cầu của cơ quan nhà nước có thẩm quyền theo quy định pháp luật."
        ]],
        ["8. Quyền của Vieco", [
            "Duyệt, từ chối hoặc gỡ hồ sơ công ty và tin tuyển dụng không đáp ứng điều khoản này.",
            "Cấp hoặc thu hồi dấu “Doanh nghiệp đã xác minh” dựa trên kết quả kiểm tra thông tin doanh nghiệp.",
            "Tạm khóa hoặc khóa vĩnh viễn tài khoản vi phạm mà không cần báo trước trong trường hợp nghiêm trọng.",
            "Tạm ngừng dịch vụ để bảo trì, nâng cấp; Vieco sẽ cố gắng thông báo trước khi có thể."
        ]],
        ["9. Giới hạn trách nhiệm", [
            "Vieco là nền tảng trung gian kết nối, không phải bên tuyển dụng và không bảo đảm ứng viên sẽ được tuyển hay doanh nghiệp sẽ tuyển được người.",
            "Vieco không chịu trách nhiệm về thỏa thuận lao động, tranh chấp phát sinh giữa ứng viên và nhà tuyển dụng, cũng như tính chính xác của nội dung do người dùng đăng tải.",
            "Nếu phát hiện tin tuyển dụng đáng ngờ, vui lòng báo cho Vieco qua trang Liên hệ để được kiểm tra."
        ]],
        ["10. Thay đổi điều khoản", [
            "Vieco có thể cập nhật Điều khoản sử dụng khi cần thiết. Phiên bản mới có hiệu lực kể từ khi được đăng trên website.",
            "Việc bạn tiếp tục sử dụng dịch vụ sau khi điều khoản thay đổi được xem là đồng ý với nội dung mới."
        ]],
        ["11. Liên hệ", [
            "Mọi câu hỏi, góp ý hoặc khiếu nại về Điều khoản sử dụng, vui lòng gửi qua trang Liên hệ của Vieco. Chúng tôi sẽ phản hồi trong thời gian sớm nhất."
        ]]
    ];

    function termsBody() {
        return TERMS.map(function (section) {
            return h("section", {},
                h("h3", { text: section[0] }),
                h("ul", {}, section[1].map(function (text) { return h("li", { text: text }); })));
        });
    }

    function openTerms() {
        V.modal(function (close) {
            var agree = h("button", { type: "button", class: "v-btn v-btn-primary v-btn-sm", disabled: true, text: "Tôi đã đọc và đồng ý" });
            var hint = h("p", { class: "terms-hint", "aria-live": "polite", text: "Vui lòng đọc hết điều khoản (cuộn xuống cuối) để đồng ý." });
            var box = h("div", { class: "terms-box", tabindex: "0", role: "document", "aria-label": "Nội dung điều khoản sử dụng" },
                termsBody(),
                h("p", { class: "terms-end", text: "Cảm ơn bạn đã dành thời gian đọc Điều khoản sử dụng của Vieco." }));
            function check() {
                if (box.scrollTop + box.clientHeight >= box.scrollHeight - 8) {
                    agree.disabled = false;
                    hint.textContent = "Bạn đã đọc hết điều khoản.";
                    box.removeEventListener("scroll", check);
                }
            }
            box.addEventListener("scroll", check);
            window.requestAnimationFrame(check); // màn hình đủ cao, không cần cuộn
            agree.addEventListener("click", function () {
                hasRead = true;
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event("change", { bubbles: true }));
                close();
                checkbox.focus();
            });
            return [
                h("p", { class: "v-eyebrow", text: "Vieco" }),
                h("h2", { text: "Điều khoản sử dụng" }),
                h("p", { class: "v-modal-sub", text: "Hiệu lực từ ngày " + EFFECTIVE_DATE + ". Áp dụng cho mọi ứng viên, nhà tuyển dụng và khách truy cập." }),
                box,
                hint,
                h("div", { class: "terms-actions" },
                    h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Đóng", onclick: close }),
                    agree)
            ];
        }, { label: "Điều khoản sử dụng", className: "terms-modal" });
    }

    document.querySelectorAll("[data-open-terms]").forEach(function (link) {
        link.addEventListener("click", function (event) {
            event.preventDefault();
            openTerms();
        });
    });
    // Tick đồng ý khi chưa đọc: mở điều khoản để đọc trước, ô chỉ được chọn sau khi bấm Đồng ý.
    checkbox.addEventListener("click", function (event) {
        if (checkbox.checked && !hasRead) {
            event.preventDefault();
            openTerms();
        }
    });
}());
