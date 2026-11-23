/* Chi tiết việc làm + form ứng tuyển (PB-021): chọn CV có sẵn hoặc tải CV mới, thư giới thiệu, chống nộp trùng. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    var jobId = new URLSearchParams(window.location.search).get("id");
    var job = null, company = null, user = null, applied = null;
    var applyButtons = [];

    function kv(label, value) { return h("div", { class: "v-kv" }, h("dt", { text: label }), h("dd", { text: value || "—" })); }
    function stat(iconName, label, value) {
        return h("div", { class: "v-stat" }, V.icon(iconName, "v-icon-lg"), h("div", {}, h("small", { text: label }), h("strong", { text: value || "—" })));
    }

    function applyButton(extraClass) {
        var button = h("button", { type: "button", class: "v-btn v-btn-primary " + (extraClass || "") }, "Ứng tuyển ngay", V.icon("out"));
        button.addEventListener("click", startApply);
        applyButtons.push(button);
        paintApply(button);
        return button;
    }
    function paintApply(button) {
        if (!applied) return;
        V.clear(button);
        button.appendChild(document.createTextNode("Đã ứng tuyển · " + V.APP_STATUS[applied.status][0]));
        button.disabled = true; // mỗi tin chỉ ứng tuyển một lần (BR-05)
    }

    function render() {
        document.title = job.title + " | Vieco";
        var save = V.saveButton(job);
        save.className = "v-btn v-btn-outline v-save-inline";
        save.style.position = "static";
        save.style.width = "auto";
        save.style.height = "54px";
        save.insertBefore(document.createTextNode("Lưu việc"), save.firstChild);

        var head = h("section", { class: "v-page-head" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" },
                h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }),
                h("a", { href: V.url("pages/jobs.html"), text: "Việc làm" }), h("span", { text: "/" }),
                h("span", { "aria-current": "page", text: job.title })),
            h("div", { class: "v-title-row" },
                V.logo(job.company_name, "", job.company_logo_url),
                h("div", { class: "grow" },
                    h("p", { class: "v-eyebrow", text: [job.industry_name, V.EMPLOYMENT[job.employment_type]].filter(Boolean).join("  ·  ") }),
                    h("h1", { text: job.title }),
                    h("div", { class: "v-meta" },
                        h("span", { class: "v-verified-inline" },
                            h("a", { class: "strong", href: V.companyUrl(job.company_id), text: job.company_name }),
                            V.verified(job.company_verified)),
                        job.province_name && h("span", {}, V.icon("pin", "v-icon-sm"), job.province_name),
                        h("span", {}, V.icon("clock", "v-icon-sm"), "Đăng " + V.ago(job.published_at || job.created_at).toLowerCase()),
                        h("span", {}, V.icon("users", "v-icon-sm"), job.application_count + " lượt ứng tuyển"))),
                h("div", { class: "v-title-actions" }, save, applyButton())),
            h("div", { class: "v-stats" },
                stat("brief", "Mức lương", V.salary(job)),
                stat("users", "Kinh nghiệm", V.EXPERIENCE[job.experience_level]),
                stat("pin", "Hình thức", V.EMPLOYMENT[job.employment_type]),
                stat("clock", "Hạn nộp hồ sơ", V.date(job.deadline)))));

        var main = h("div", {},
            !user || user.role === "CANDIDATE" ? matchSection() : null,
            h("section", { class: "v-block" }, h("h2", { text: "Mô tả công việc" }), V.prose(job.description)),
            h("section", { class: "v-block" }, h("h2", { text: "Yêu cầu ứng viên" }), V.prose(job.requirements)),
            h("section", { class: "v-block" }, h("h2", { text: "Quyền lợi" }), V.prose(job.benefits)),
            job.skills.length ? h("section", { class: "v-block" }, h("h2", { text: "Kỹ năng" }),
                h("div", { class: "v-chips" }, job.skills.map(function (s) {
                    return h("a", { class: "v-chip v-chip-lg", href: V.url("pages/jobs.html") + "?q=" + encodeURIComponent(s.name), text: s.name });
                }))) : null,
            h("div", { class: "v-banner" },
                h("div", {}, h("h3", { text: "Bạn thấy mình phù hợp?" }), h("p", { text: "Gửi hồ sơ ngay hôm nay. Chỉ mất 2 phút với CV trên Vieco." })),
                applyButton("v-btn-sm")));

        var brand = h("strong", { class: "v-h3", text: V.brand(job.company_name) });
        brand.style.color = V.brandColor(job.company_name);
        brand.style.fontWeight = "700";
        var side = h("aside", {},
            h("div", { class: "v-card v-photo-card", style: "padding:0" },
                company && V.media(company.cover_url) ? h("img", { src: V.media(company.cover_url), alt: "Ảnh bìa " + job.company_name }) : null,
                h("div", { style: "padding:24px" },
                    h("div", { class: "v-card-title" }, h("span", { class: "v-verified-inline" }, brand, V.verified(job.company_verified)),
                        h("a", { class: "v-link v-small", href: V.companyUrl(job.company_id), text: "Xem công ty ↗" })),
                    h("p", { class: "v-small v-muted v-mb-2", text: company && company.description ? V.lines(company.description)[0] : job.company_name }),
                    h("dl", {},
                        kv("Lĩnh vực", company && company.industry_name),
                        kv("Quy mô", company && company.size ? company.size + " nhân viên" : null),
                        kv("Trụ sở", company && company.province_name),
                        kv("Đang tuyển", company ? company.open_jobs + " vị trí" : null)))),
            h("div", { class: "v-card" },
                h("h2", { class: "v-card-title", text: "Thông tin chung" }),
                h("dl", {},
                    kv("Số lượng tuyển", job.positions + " người"),
                    kv("Nơi làm việc", job.work_address || job.province_name),
                    kv("Ngày đăng", V.date(job.published_at || job.created_at)),
                    kv("Lượt xem", String(job.view_count)))),
            h("p", { class: "v-small v-muted v-mt-2" }, "Chia sẻ việc làm:  ",
                h("button", { type: "button", class: "v-link", text: "Sao chép liên kết ↗", onclick: function () {
                    var done = function () { V.toast("Đã sao chép liên kết"); };
                    if (navigator.clipboard) navigator.clipboard.writeText(window.location.href).then(done, function () { V.toast("Không sao chép được, hãy sao chép từ thanh địa chỉ", true); });
                    else V.toast("Hãy sao chép liên kết từ thanh địa chỉ", true);
                } })));

        var similar = h("div", { class: "v-grid-3" });
        var similarSection = h("section", { class: "v-section v-section-cream", hidden: true }, h("div", { class: "v-wrap" },
            h("div", { class: "v-section-head" },
                h("div", {}, h("p", { class: "v-eyebrow", text: "Có thể bạn quan tâm" }), h("h2", { class: "v-h2", text: "Việc làm tương tự" })),
                h("a", { class: "v-link", href: V.url("pages/jobs.html"), text: "Xem tất cả việc làm  ↗" })),
            similar));

        V.clear(app);
        app.appendChild(head);
        app.appendChild(h("section", { class: "v-section" }, h("div", { class: "v-wrap v-layout-side" }, main, side)));
        app.appendChild(similarSection);

        V.api("/jobs", { auth: false, query: { industry_id: job.industry_id, page_size: 4 } }).then(function (data) {
            var items = data.items.filter(function (item) { return item.id !== job.id; }).slice(0, 3);
            items.forEach(function (item) { similar.appendChild(V.jobCard(item)); });
            similarSection.hidden = items.length === 0;
        }).catch(function () {});
    }

    // ---------- Trợ lý AI: độ phù hợp của CV với tin và tối ưu CV theo tin ----------
    var MATCH_KEY = "vieco.match.v1:";
    var match = { body: null, analyzeButton: null, tailorButton: null, busy: false, hasResult: false };

    function readMatch() {
        try {
            var saved = JSON.parse(window.sessionStorage.getItem(MATCH_KEY + job.id) || "null");
            return saved && user && saved.user === user.id ? saved.result : null;
        } catch (_) { return null; }
    }
    function storeMatch(result) {
        try { window.sessionStorage.setItem(MATCH_KEY + job.id, JSON.stringify({ user: user.id, result: result })); } catch (_) { /* bỏ qua */ }
    }
    function readable(cv) { return cv.has_builder_data || /\.pdf$/i.test(cv.file_name); } // AI đọc được CV trực tuyến hoặc PDF

    /** Chọn CV cho AI. Chỉ có một CV đọc được thì dùng luôn. Trả về CV hoặc null nếu người dùng hủy. */
    async function pickCv(title, actionLabel) {
        if (!user) { V.goLogin(); return null; }
        var data;
        try { data = await V.api("/candidates/me/cvs"); } catch (error) { V.toast(error.message, true); return null; }
        var usable = data.items.filter(readable);
        if (!usable.length) {
            V.modal(function (close) {
                return [
                    h("p", { class: "v-eyebrow", text: "Trợ lý AI" }),
                    h("h2", { text: data.items.length ? "AI chưa đọc được CV của bạn" : "Bạn chưa có CV" }),
                    h("p", { class: "v-modal-sub", text: data.items.length
                        ? "AI đọc được CV dạng PDF hoặc CV tạo bằng trình tạo CV của Vieco. Các CV hiện có của bạn là tệp Word."
                        : "Tạo CV trực tuyến hoặc tải CV dạng PDF lên để AI phân tích và tối ưu theo tin tuyển dụng." }),
                    h("div", { class: "v-field-row" },
                        h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Đóng", onclick: close }),
                        h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/cv-builder.html"), text: "Tạo CV ngay" }))
                ];
            }, { small: true, label: "Chưa có CV phù hợp" });
            return null;
        }
        if (data.items.length === 1) return usable[0];
        var preferred = usable.filter(function (cv) { return cv.is_default; })[0] || usable[0];
        return new Promise(function (resolve) {
            V.modal(function (close) {
                var options = h("div", { class: "v-options v-cv-pick", style: "grid-template-columns:1fr" }, data.items.map(function (cv) {
                    var ok = readable(cv);
                    var kind = cv.has_builder_data ? "CV tạo trên Vieco" : ok ? "CV tải lên (PDF)" : "Tệp Word: AI chưa đọc được";
                    return h("label", { class: "v-option" + (ok ? "" : " is-disabled") },
                        h("input", { type: "radio", name: "ai-cv", value: String(cv.id), checked: cv === preferred, disabled: !ok }),
                        V.icon("file", "v-icon-lg"),
                        h("span", {}, h("strong", { text: cv.file_name }), h("small", { text: kind + (cv.is_default ? " · mặc định" : "") })));
                }));
                var form = h("form", { novalidate: true },
                    h("p", { class: "v-eyebrow", text: "Trợ lý AI" }), h("h2", { text: title }),
                    h("p", { class: "v-modal-sub", text: job.title + (job.company_name ? "  ·  " + job.company_name : "") }),
                    options,
                    h("p", { class: "v-small v-muted v-mt-2", text: "Nội dung CV được gửi tới dịch vụ AI (Claude của Anthropic) để phân tích." }),
                    h("div", { class: "v-form-foot" }, h("span", {}), h("div", { class: "actions" },
                        h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Hủy", onclick: close }),
                        h("button", { type: "submit", class: "v-btn v-btn-primary v-btn-sm" }, V.icon("spark"), actionLabel))));
                form.addEventListener("submit", function (event) {
                    event.preventDefault();
                    var id = (form.querySelector('input[name="ai-cv"]:checked') || {}).value;
                    var chosen = usable.filter(function (cv) { return String(cv.id) === id; })[0];
                    if (!chosen) return;
                    resolve(chosen);
                    close();
                });
                return form;
            }, { label: title, onClose: function () { resolve(null); } });
        });
    }

    function paintMatchButtons() {
        match.analyzeButton.disabled = match.tailorButton.disabled = match.busy;
        V.clear(match.analyzeButton);
        match.analyzeButton.appendChild(V.icon("spark"));
        match.analyzeButton.appendChild(document.createTextNode(match.hasResult ? "Phân tích lại" : "Phân tích độ phù hợp"));
    }
    async function analyze(cv) {
        if (match.busy) return;
        cv = cv || await pickCv("Chọn CV để AI phân tích", "Phân tích");
        if (!cv) return;
        match.busy = true;
        paintMatchButtons();
        V.clear(match.body).appendChild(h("div", { class: "v-match-loading", role: "status" },
            h("span", { class: "dots", "aria-hidden": "true" }, h("span"), h("span"), h("span")),
            "AI đang đọc “" + cv.file_name + "” và so sánh với yêu cầu của tin..."));
        try {
            var result = await V.api("/candidates/me/job-match", { method: "POST", body: { job_id: job.id, cv_id: cv.id }, timeout: 120000 });
            storeMatch(result);
            showMatch(result, true);
        } catch (error) {
            V.clear(match.body);
            V.note(match.body, error.message, "error");
        }
        match.busy = false;
        paintMatchButtons();
    }
    async function tailor(cv) {
        if (match.busy) return;
        cv = cv || await pickCv("Chọn CV để AI tối ưu", "Tối ưu CV");
        if (!cv) return;
        window.location.href = V.url("pages/cv-builder.html") + "?tailor_job=" + encodeURIComponent(job.id) + "&from_cv=" + encodeURIComponent(cv.id);
    }

    function matchLevel(score) {
        if (score >= 85) return ["Rất phù hợp", "is-high"];
        if (score >= 70) return ["Phù hợp", "is-good"];
        if (score >= 50) return ["Tương đối phù hợp", "is-mid"];
        return ["Chưa phù hợp", "is-low"];
    }
    function matchList(items, empty) {
        return items.length ? h("ul", {}, items.map(function (text) { return h("li", { text: text }); })) : h("p", { class: "v-muted", text: empty });
    }
    function matchChips(items, cls, empty) {
        return items.length ? h("div", { class: "v-chips" }, items.map(function (text) { return h("span", { class: "v-chip " + cls, text: text }); }))
            : h("p", { class: "v-muted", text: empty });
    }
    function box(iconName, title, content) {
        return h("div", { class: "v-match-box" }, h("h3", {}, V.icon(iconName, "v-icon-sm"), title), content);
    }
    function showMatch(result, animate) {
        match.hasResult = true;
        var level = matchLevel(result.score);
        var number = h("strong", {}, "0", h("small", { text: "%" }));
        var ring = h("div", { class: "v-match-ring " + level[1], role: "img", "aria-label": "Mức độ phù hợp " + result.score + "%" }, number);
        function set(value) { ring.style.setProperty("--score", value); number.firstChild.nodeValue = String(value); }
        var still = !animate || !window.requestAnimationFrame || (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
        if (still) set(result.score);
        else {
            var start = null;
            window.requestAnimationFrame(function step(time) {
                start = start || time;
                var progress = Math.min(1, (time - start) / 900);
                set(Math.round(result.score * (1 - Math.pow(1 - progress, 3))));
                if (progress < 1) window.requestAnimationFrame(step);
            });
        }
        var cv = { id: result.cv_id, file_name: result.cv_name };
        V.clear(match.body);
        match.body.appendChild(h("div", { class: "v-match-summary" }, ring,
            h("div", {},
                h("p", { class: "v-match-level", text: level[0] }),
                h("p", { class: "v-match-verdict", text: result.verdict }),
                h("p", { class: "v-match-meta" }, V.icon("file", "v-icon-sm"), "Phân tích với CV “" + result.cv_name + "”",
                    h("button", { type: "button", class: "v-link", text: "Dùng CV khác ↗", onclick: function () { analyze(); } })))));
        match.body.appendChild(h("div", { class: "v-match-grid" },
            box("check", "Bạn đáp ứng", matchChips(result.matched_skills, "v-chip-ok", "AI chưa thấy yêu cầu nào được thể hiện rõ trong CV.")),
            box("plus", "Còn thiếu", matchChips(result.missing_skills, "v-chip-miss", "CV đã thể hiện đủ các yêu cầu chính."))));
        match.body.appendChild(h("div", { class: "v-match-grid" },
            box("users", "Điểm mạnh", matchList(result.strengths, "Chưa có nhận xét.")),
            box("search", "Cần bổ sung", matchList(result.gaps, "Không có điểm cần bổ sung."))));
        if (result.tips.length) match.body.appendChild(h("div", { class: "v-match-box v-match-tips" },
            h("h3", {}, V.icon("spark", "v-icon-sm"), "Gợi ý cho bạn"), matchList(result.tips, "")));
        var next = h("div", { class: "v-match-next" },
            h("button", { type: "button", class: "v-btn v-btn-gold v-btn-sm", onclick: function () { tailor(cv); } }, V.icon("edit"), "Tối ưu CV này cho vị trí"));
        if (!applied) next.appendChild(applyButton("v-btn-sm"));
        match.body.appendChild(next);
        match.body.appendChild(h("p", { class: "v-match-disclaimer", text: "Kết quả do AI đánh giá dựa trên nội dung CV và tin tuyển dụng, chỉ mang tính tham khảo. Nhà tuyển dụng không xem được kết quả này." }));
    }
    function matchSection() {
        match.body = h("div", { class: "v-match-body", "aria-live": "polite" });
        match.analyzeButton = h("button", { type: "button", class: "v-btn v-btn-primary v-btn-sm", onclick: function () { analyze(); } });
        match.tailorButton = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", onclick: function () { tailor(); } }, V.icon("edit"), "Tối ưu CV cho vị trí này");
        var section = h("section", { class: "v-match", "aria-labelledby": "match-title" },
            h("div", { class: "v-match-head" },
                h("span", { class: "v-match-icon", "aria-hidden": "true" }, V.icon("spark", "v-icon-lg")),
                h("div", {},
                    h("p", { class: "v-eyebrow", text: "Trợ lý AI · Dành cho ứng viên" }),
                    h("h2", { id: "match-title", text: "Bạn phù hợp với vị trí này đến đâu?" }),
                    h("p", { text: user ? "AI so sánh CV của bạn với yêu cầu của tin: chấm điểm phù hợp, chỉ ra kỹ năng còn thiếu và gợi ý cách tăng cơ hội trúng tuyển. Bạn cũng có thể để AI chỉnh CV cho khớp với vị trí này."
                        : "Đăng nhập tài khoản ứng viên để AI chấm điểm CV của bạn với tin này và gợi ý cách chỉnh CV cho khớp với vị trí." }))),
            h("div", { class: "v-match-actions" }, match.analyzeButton, match.tailorButton),
            match.body);
        paintMatchButtons();
        var saved = user ? readMatch() : null;
        if (saved) showMatch(saved, false);
        paintMatchButtons();
        return section;
    }

    // ---------- Ứng tuyển ----------
    async function startApply() {
        if (!user) return V.goLogin();
        if (user.role !== "CANDIDATE") return V.toast("Chỉ tài khoản ứng viên mới ứng tuyển được", true);
        var cvs;
        try {
            cvs = await V.api("/candidates/me/cvs");
        } catch (error) { return V.toast(error.message, true); }
        openApplyModal(cvs);
    }

    function openApplyModal(cvData) {
        var message = h("div", {});
        var name = h("input", { type: "text", name: "full_name", value: user.full_name || "", required: true, maxlength: 150, autocomplete: "name" });
        var phone = h("input", { type: "tel", name: "phone", value: user.phone || "", placeholder: "0901234567", autocomplete: "tel" });
        var email = h("input", { type: "email", value: user.email, disabled: true });
        var file = h("input", { type: "file", accept: "." + cvData.allowed_extensions.join(",."), hidden: true });
        var uploadTitle = h("strong", { text: "Tải CV từ máy tính" });
        var uploadRadio = h("input", { type: "radio", name: "cv", value: "upload", checked: cvData.items.length === 0 });
        var canUpload = cvData.total < cvData.max_count;
        var options = h("div", { class: "v-options" },
            cvData.items.map(function (cv, index) {
                return h("label", { class: "v-option" },
                    h("input", { type: "radio", name: "cv", value: String(cv.id), checked: cv.is_default || (index === 0 && !cvData.items.some(function (c) { return c.is_default; })) }),
                    V.icon("file", "v-icon-lg"),
                    h("span", {}, h("strong", { text: cv.file_name }), h("small", { text: "Tải lên " + V.ago(cv.created_at).toLowerCase() + (cv.is_default ? " · mặc định" : "") })));
            }),
            canUpload ? h("label", { class: "v-option" }, uploadRadio, V.icon("upload", "v-icon-lg"),
                h("span", {}, uploadTitle, h("small", { text: cvData.allowed_extensions.join(", ").toUpperCase() + " · tối đa " + cvData.max_size_mb + "MB" })), file) : null);
        if (canUpload) {
            uploadRadio.addEventListener("click", function () { file.click(); });
            file.addEventListener("change", function () {
                uploadTitle.textContent = file.files[0] ? file.files[0].name : "Tải CV từ máy tính";
                uploadRadio.checked = true;
            });
        }
        var letter = h("textarea", { name: "cover_letter", maxlength: 5000, rows: 4, placeholder: "Viết đôi lời giới thiệu bản thân và lý do bạn phù hợp với vị trí này..." });
        var submit = h("button", { type: "submit", class: "v-btn v-btn-primary v-btn-sm" }, "Gửi hồ sơ", V.icon("out"));
        var uploadedCv = null;
        file.addEventListener("change", function () { uploadedCv = null; });

        V.modal(function (close) {
            var form = h("form", { novalidate: true },
                h("p", { class: "v-eyebrow", text: "Ứng tuyển vị trí" }),
                h("h2", { text: job.title }),
                h("p", { class: "v-modal-sub", text: [job.company_name, job.province_name, V.salary(job)].filter(Boolean).join("  ·  ") }),
                message,
                h("div", { class: "v-field-row" },
                    h("label", { class: "v-field" }, h("span", { text: "Họ và tên" }), name),
                    h("label", { class: "v-field" }, h("span", { text: "Số điện thoại" }), phone)),
                h("label", { class: "v-field" }, h("span", { text: "Email" }), email),
                h("div", { class: "v-field" }, h("span", { class: "v-label", text: "CV ứng tuyển" }), options,
                    !canUpload && h("p", { class: "v-small v-muted v-mt-2", text: "Bạn đã có tối đa " + cvData.max_count + " CV. Hãy xóa bớt trong hồ sơ để tải CV mới." })),
                h("label", { class: "v-field" }, h("span", { text: "Thư giới thiệu (không bắt buộc)" }), letter),
                h("div", { class: "v-form-foot" },
                    h("p", { class: "v-small v-muted", style: "max-width:300px", text: "Bằng việc gửi hồ sơ, bạn đồng ý với Điều khoản sử dụng của Vieco." }),
                    h("div", { class: "actions" },
                        h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Hủy", onclick: close }), submit)));

            form.addEventListener("submit", async function (event) {
                event.preventDefault();
                if (submit.disabled) return;
                var fullName = name.value.trim(), phoneValue = phone.value.trim();
                var choice = (form.querySelector('input[name="cv"]:checked') || {}).value;
                if (fullName.length < 2) return V.note(message, "Vui lòng nhập họ và tên (ít nhất 2 ký tự).", "error");
                if (phoneValue && !/^\+?\d{9,15}$/.test(phoneValue)) return V.note(message, "Số điện thoại không hợp lệ.", "error");
                if (!choice) return V.note(message, "Vui lòng chọn một CV để ứng tuyển.", "error");
                if (choice === "upload" && !file.files[0]) return V.note(message, "Vui lòng chọn tệp CV từ máy tính.", "error");
                if (choice === "upload" && file.files[0].size > cvData.max_size_mb * 1024 * 1024) {
                    return V.note(message, "Tệp CV vượt quá " + cvData.max_size_mb + "MB.", "error");
                }
                submit.disabled = true;
                V.note(message, "Đang gửi hồ sơ...");
                try {
                    if (fullName !== user.full_name || phoneValue !== (user.phone || "")) {
                        await V.api("/users/profile", { method: "PUT", body: { full_name: fullName, phone: phoneValue || null } });
                        user.full_name = fullName;
                        user.phone = phoneValue || null;
                    }
                    var cvId = choice, cvName;
                    if (choice === "upload") {
                        if (!uploadedCv) {
                            var data = new FormData();
                            data.append("file", file.files[0]);
                            uploadedCv = await V.api("/candidates/me/cvs", { method: "POST", formData: data });
                        }
                        cvId = uploadedCv.id;
                        cvName = uploadedCv.file_name;
                    }
                    var result = await V.api("/applications", { method: "POST", body: {
                        job_id: job.id, cv_id: Number(cvId), cover_letter: letter.value.trim() || null } });
                    applied = result;
                    applyButtons.forEach(paintApply);
                    close();
                    openSuccess(result, cvName || result.cv_file_name);
                } catch (error) {
                    V.note(message, error.message, "error");
                    submit.disabled = false;
                }
            });
            return form;
        }, { label: "Ứng tuyển " + job.title });
    }

    function openSuccess(result, cvName) {
        var code = "VC-" + new Date().getFullYear() + "-" + String(result.id).padStart(5, "0");
        V.modal(function (close) {
            return [
                h("div", { class: "v-modal-check" }, V.icon("check", "v-icon-xl")),
                h("p", { class: "v-eyebrow", text: "Hồ sơ đã được gửi" }),
                h("h2", { text: "Ứng tuyển thành công!" }),
                h("p", { class: "v-lead", text: "Nhà tuyển dụng sẽ xem hồ sơ của bạn. Bạn có thể theo dõi trạng thái trong mục Việc đã ứng tuyển." }),
                h("dl", { class: "v-summary" }, kv("Vị trí", job.title), kv("Công ty", job.company_name), kv("CV đã gửi", cvName), kv("Mã hồ sơ", code)),
                h("div", { class: "v-field-row" },
                    h("a", { class: "v-btn v-btn-outline v-btn-sm", href: V.url("pages/profile.html#applications"), text: "Việc đã ứng tuyển" }),
                    h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/jobs.html") }, "Tiếp tục tìm việc", V.icon("out")))
            ];
        }, { small: true, label: "Ứng tuyển thành công" });
    }

    async function init() {
        if (!jobId) {
            return V.empty(app, "Không tìm thấy tin tuyển dụng", "Đường dẫn thiếu mã tin.", h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/jobs.html"), text: "Xem việc làm khác" }));
        }
        try {
            job = await V.api("/jobs/" + encodeURIComponent(jobId), { auth: false });
        } catch (error) {
            var wrap = h("div", { class: "v-wrap v-section" });
            V.clear(app).appendChild(wrap);
            return V.empty(wrap, error.status === 404 ? "Tin tuyển dụng không còn hiển thị" : "Không tải được tin tuyển dụng",
                error.status === 404 ? "Tin có thể đã hết hạn, đã đóng hoặc bị gỡ." : error.message,
                h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/jobs.html"), text: "Xem việc làm khác" }));
        }
        user = await V.currentUser();
        var tasks = [V.api("/companies/" + job.company_id, { auth: false }).then(function (c) { company = c; }).catch(function () {})];
        if (user && user.role === "CANDIDATE") {
            tasks.push(V.api("/applications/my-applications", { query: { page_size: 100 } }).then(function (data) {
                applied = data.items.filter(function (a) { return a.job_id === job.id; })[0] || null;
            }).catch(function () {}));
        }
        await Promise.all(tasks);
        render();
        if (window.location.hash === "#apply" && !applied) startApply();
    }
    init().catch(function (error) { V.note(app, error.message, "error"); });
}());
