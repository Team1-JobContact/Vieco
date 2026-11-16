/* Trang công ty công khai (FR-M1-14): giới thiệu, thông tin liên hệ và các vị trí đang tuyển. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    var id = new URLSearchParams(window.location.search).get("id");

    function stat(iconName, label, value) {
        return h("div", { class: "v-stat" }, V.icon(iconName, "v-icon-lg"), h("div", {}, h("small", { text: label }), h("strong", { text: value || "—" })));
    }
    function contact(iconName, label, value) {
        return h("div", { class: "v-kv", style: "justify-content:flex-start;align-items:flex-start" }, V.icon(iconName),
            h("div", { style: "min-width:0" }, h("dt", { class: "v-small", text: label }), h("dd", { style: "text-align:left" }, value)));
    }
    function fail(title, text) {
        var wrap = h("div", { class: "v-wrap v-section" });
        V.clear(app).appendChild(wrap);
        V.empty(wrap, title, text, h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/companies.html"), text: "Xem các công ty khác" }));
    }

    async function init() {
        if (!id) return fail("Không tìm thấy công ty", "Đường dẫn thiếu mã công ty.");
        var company, jobs;
        try {
            company = await V.api("/companies/" + encodeURIComponent(id), { auth: false });
            jobs = await V.api("/jobs", { auth: false, query: { company_id: company.id, page_size: 6 } });
        } catch (error) {
            return fail(error.status === 404 ? "Công ty không tồn tại hoặc chưa được duyệt" : "Không tải được thông tin công ty", error.status === 404 ? "" : error.message);
        }
        document.title = company.name + " | Vieco";
        var link = V.linkInfo(company.website);
        var coverSrc = V.media(company.cover_url);
        var photos = (company.images || []).map(function (image) { return V.media(image.url); }).filter(Boolean);
        var jobsId = "company-jobs";

        V.clear(app);
        if (coverSrc) app.appendChild(h("img", { class: "v-cover", src: coverSrc, alt: "Ảnh bìa " + company.name }));
        app.appendChild(h("section", { class: "v-page-head", style: "background:var(--v-bg);padding-bottom:0" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" },
                h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }),
                h("a", { href: V.url("pages/companies.html"), text: "Công ty" }), h("span", { text: "/" }),
                h("span", { "aria-current": "page", text: company.name })),
            h("div", { class: "v-title-row" },
                V.logo(company.name, "", company.logo_url),
                h("div", { class: "grow" },
                    h("p", { class: "v-eyebrow", text: company.industry_name || "Doanh nghiệp" }),
                    h("h1", { text: company.name }),
                    h("div", { class: "v-meta" }, company.province_name && h("span", {}, V.icon("pin", "v-icon-sm"), company.province_name),
                        h("span", {}, V.icon("shield", "v-icon-sm"), "Đã được Vieco xác minh"))),
                h("div", { class: "v-title-actions" },
                    h("a", { class: "v-btn v-btn-primary", href: "#" + jobsId }, "Xem " + company.open_jobs + " việc làm", V.icon("out")))),
            h("div", { class: "v-stats" },
                stat("users", "Quy mô", company.size ? company.size + " nhân viên" : null),
                stat("brief", "Lĩnh vực", company.industry_name),
                stat("pin", "Trụ sở", company.province_name),
                stat("trend", "Đang tuyển", company.open_jobs + " vị trí")))));

        app.appendChild(h("section", { class: "v-section" }, h("div", { class: "v-wrap v-layout-side" },
            h("div", {},
                h("section", { class: "v-block" }, h("h2", { text: "Về " + company.name }),
                    company.description ? h("div", { class: "v-prose" }, V.lines(company.description).map(function (l) { return h("p", { text: l }); }))
                        : h("p", { class: "v-muted", text: "Công ty chưa cập nhật phần giới thiệu." })),
                photos.length ? h("section", { class: "v-block" }, h("h2", { text: "Không gian làm việc" }),
                    h("div", { class: "v-gallery" }, photos.map(function (src, index) {
                        return h("a", { href: src, target: "_blank", rel: "noopener noreferrer", "aria-label": "Mở ảnh không gian làm việc " + (index + 1) },
                            h("img", { src: src, alt: "Không gian làm việc tại " + company.name + " (" + (index + 1) + ")", loading: "lazy" }));
                    }))) : null),
            h("aside", {},
                h("div", { class: "v-card" }, h("h2", { class: "v-card-title", text: "Thông tin liên hệ" }),
                    h("dl", {},
                        contact("globe", link ? link.kind : "Website", link ? V.externalLink(company.website) : "Chưa cập nhật"),
                        contact("pin", "Trụ sở chính", [company.address, company.province_name].filter(Boolean).join(", ") || "Chưa cập nhật"))),
                h("div", { class: "v-banner", style: "display:block;margin-top:24px" },
                    h("h3", { text: "Đừng bỏ lỡ cơ hội mới" }),
                    h("p", { text: "Xem các vị trí " + company.name + " đang tuyển và ứng tuyển ngay hôm nay." }),
                    h("a", { class: "v-btn v-btn-primary v-btn-sm v-btn-block v-mt-2", href: "#" + jobsId, text: "Xem vị trí đang tuyển" }))))));

        var grid = h("div", { class: "v-grid-3" });
        app.appendChild(h("section", { class: "v-section v-section-cream", id: jobsId }, h("div", { class: "v-wrap" },
            h("div", { class: "v-section-head" },
                h("div", {}, h("p", { class: "v-eyebrow", text: "Gia nhập đội ngũ" }), h("h2", { class: "v-h2", text: "Vị trí đang tuyển tại " + V.brand(company.name) })),
                jobs.total > jobs.items.length ? h("a", { class: "v-link", href: V.url("pages/jobs.html") + "?q=" + encodeURIComponent(company.name), text: "Xem tất cả " + jobs.total + " việc làm  ↗" }) : null),
            grid)));
        if (!jobs.items.length) { grid.style.display = "block"; V.empty(grid, "Công ty chưa có vị trí đang tuyển", "Hãy quay lại sau hoặc khám phá việc làm khác."); }
        else jobs.items.forEach(function (job) { grid.appendChild(V.jobCard(job)); });
    }
    init();
}());
