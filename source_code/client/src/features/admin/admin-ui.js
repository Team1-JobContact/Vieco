/* Trang quản trị (PB-017): duyệt/từ chối công ty và tin tuyển dụng, bắt buộc lý do khi từ chối, xem lý do đã ghi. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    var content, message, tabsBox, counters = {};
    var TABS = [["companies", "Duyệt công ty"], ["jobs", "Duyệt tin tuyển dụng"]];

    function currentTab() { return window.location.hash === "#jobs" ? "jobs" : "companies"; }
    function kv(label, value) { return h("div", { class: "v-kv" }, h("dt", { text: label }), h("dd", { text: value || "—" })); }

    /** Hộp thoại nhập lý do (10–500 ký tự) dùng cho từ chối công ty, từ chối tin và gỡ tin. */
    function reasonDialog(title, subject, confirmLabel) {
        return new Promise(function (resolve) {
            var result = null;
            V.modal(function (close) {
                var input = h("textarea", { rows: 4, maxlength: 500, required: true, placeholder: "Nêu rõ lý do để nhà tuyển dụng chỉnh sửa và gửi lại (10–500 ký tự)" });
                var error = h("div", {});
                var form = h("form", { novalidate: true }, h("p", { class: "v-eyebrow", text: title }), h("h2", { text: subject }),
                    h("p", { class: "v-modal-sub", text: "Lý do sẽ được gửi cho nhà tuyển dụng qua thông báo." }), error,
                    h("label", { class: "v-field" }, h("span", { text: "Lý do" }), input),
                    h("div", { class: "v-form-foot" }, h("span", {}), h("div", { class: "actions" },
                        h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Hủy", onclick: close }),
                        h("button", { type: "submit", class: "v-btn v-btn-danger v-btn-sm", text: confirmLabel }))));
                form.addEventListener("submit", function (event) {
                    event.preventDefault();
                    var value = input.value.trim();
                    if (value.length < 10) return V.note(error, "Lý do phải có ít nhất 10 ký tự.", "error");
                    result = value;
                    close();
                });
                return form;
            }, { label: title, onClose: function () { resolve(result); } });
        });
    }

    async function run(request, done, reload) {
        try {
            await request();
            V.note(message, done, "success");
            reload();
            refreshCounters();
        } catch (error) { V.note(message, error.message, "error"); }
    }

    function toolbar(statusMap, state, onChange, placeholder) {
        var timer = null;
        var select = h("select", { "aria-label": "Lọc theo trạng thái" }, h("option", { value: "", text: "Tất cả" }),
            Object.keys(statusMap).map(function (key) { return h("option", { value: key, text: statusMap[key][0], selected: state.status === key }); }));
        var search = h("input", { class: "v-input", type: "search", placeholder: placeholder, "aria-label": placeholder, style: "height:44px;width:280px;max-width:100%" });
        select.addEventListener("change", function () { state.status = select.value; state.page = 1; onChange(); });
        search.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { state.q = search.value.trim(); state.page = 1; onChange(); }, 300); });
        return h("div", { class: "v-flex" }, search, h("label", { class: "v-select-inline" }, "Trạng thái:", select));
    }

    // ---------- Công ty ----------
    function renderCompanies() {
        var state = { status: "PENDING", q: "", page: 1 };
        var table = h("div", {}), pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang" });
        V.clear(content);
        content.appendChild(h("div", { class: "v-results-head" }, h("h2", { class: "v-h3", text: "Hồ sơ công ty" }), toolbar(V.COMPANY_STATUS, state, load, "Tìm theo tên công ty hoặc email")));
        content.appendChild(table);
        content.appendChild(pager);

        function detail(company) {
            V.modal(function (close) {
                var pending = company.status === "PENDING";
                return [
                    h("p", { class: "v-eyebrow", text: "Hồ sơ công ty" }), h("h2", { text: company.name }),
                    h("p", { class: "v-modal-sub" }, V.badge(V.COMPANY_STATUS, company.status)),
                    company.status === "REJECTED" && h("div", { class: "v-note v-note-error", text: "Lý do từ chối: " + (company.reject_reason || "") }),
                    h("dl", { class: "v-summary", style: "margin-top:0" },
                        kv("Chủ sở hữu", company.owner_name), kv("Email", company.owner_email), kv("Quy mô", company.size),
                        h("div", { class: "v-kv" }, h("dt", { text: "Website / Fanpage" }), h("dd", {}, V.externalLink(company.website) || "—")), kv("Địa chỉ", company.address), kv("Ngày tạo", V.date(company.created_at)),
                        kv("Ngày xét duyệt", company.reviewed_at ? V.date(company.reviewed_at) : null)),
                    h("h3", { class: "v-card-title", text: "Giới thiệu" }),
                    h("p", { class: "v-small", style: "white-space:pre-wrap", text: company.description || "Chưa có mô tả." }),
                    h("div", { class: "v-form-foot v-mt-3" }, h("span", {}), h("div", { class: "actions" },
                        pending && h("button", { type: "button", class: "v-btn v-btn-danger v-btn-sm", text: "Từ chối", onclick: function () { close(); reject(company); } }),
                        pending && h("button", { type: "button", class: "v-btn v-btn-primary v-btn-sm", text: "Duyệt công ty", onclick: function () { close(); approve(company); } }),
                        !pending && h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Đóng", onclick: close })))
                ];
            }, { label: "Hồ sơ công ty " + company.name });
        }
        function approve(company) {
            run(function () { return V.api("/admin/companies/" + company.id + "/approve", { method: "POST" }); }, "Đã duyệt công ty “" + company.name + "”.", load);
        }
        async function reject(company) {
            var reason = await reasonDialog("Từ chối hồ sơ công ty", company.name, "Từ chối hồ sơ");
            if (reason) run(function () { return V.api("/admin/companies/" + company.id + "/reject", { method: "POST", body: { reason: reason } }); }, "Đã từ chối công ty “" + company.name + "”.", load);
        }
        async function load() {
            V.loading(table);
            try {
                var data = await V.api("/admin/companies", { query: { status: state.status, q: state.q, page: state.page, page_size: 10 } });
                V.clear(table);
                if (!data.items.length) return V.empty(table, state.status === "PENDING" ? "Không có hồ sơ công ty chờ duyệt" : "Không có công ty phù hợp", "");
                table.appendChild(h("div", { class: "v-table-wrap" }, h("table", { class: "v-table" },
                    h("thead", {}, h("tr", {}, ["Công ty", "Chủ sở hữu", "Ngày tạo", "Trạng thái", ""].map(function (t) { return h("th", { scope: "col", text: t }); }))),
                    h("tbody", {}, data.items.map(function (company) {
                        var pending = company.status === "PENDING";
                        return h("tr", {},
                            h("td", {}, h("strong", { text: company.name }), h("small", { text: [company.size && company.size + " nhân viên", company.address].filter(Boolean).join(" · ") })),
                            h("td", {}, h("strong", { text: company.owner_name || "—" }), h("small", { text: company.owner_email || "" })),
                            h("td", { class: "v-nowrap", text: V.date(company.created_at) }),
                            h("td", {}, V.badge(V.COMPANY_STATUS, company.status),
                                company.status === "REJECTED" && h("small", { style: "display:block;margin-top:6px;max-width:240px", text: "Lý do: " + (company.reject_reason || "") })),
                            h("td", {}, h("div", { class: "v-row-actions" },
                                h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", text: "Xem", "aria-label": "Xem hồ sơ " + company.name, onclick: function () { detail(company); } }),
                                pending && h("button", { type: "button", class: "v-btn v-btn-primary v-btn-xs", text: "Duyệt", "aria-label": "Duyệt " + company.name, onclick: function () { approve(company); } }),
                                pending && h("button", { type: "button", class: "v-btn v-btn-danger v-btn-xs", text: "Từ chối", "aria-label": "Từ chối " + company.name, onclick: function () { reject(company); } }))));
                    })))));
                V.pagination(pager, data.page, Math.ceil(data.total / data.page_size), function (next) { state.page = next; load(); });
            } catch (error) { V.clear(pager); V.note(table, error.message, "error"); }
        }
        load();
    }

    // ---------- Tin tuyển dụng ----------
    function renderJobs() {
        var state = { status: "PENDING", q: "", page: 1 };
        var table = h("div", {}), pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang" });
        V.clear(content);
        content.appendChild(h("div", { class: "v-results-head" }, h("h2", { class: "v-h3", text: "Tin tuyển dụng" }), toolbar(V.JOB_STATUS, state, load, "Tìm theo tiêu đề tin")));
        content.appendChild(table);
        content.appendChild(pager);

        function approve(job) {
            run(function () { return V.api("/admin/jobs/" + job.id + "/approve", { method: "POST" }); }, "Đã duyệt tin “" + job.title + "”.", load);
        }
        async function reject(job) {
            var reason = await reasonDialog("Từ chối tin tuyển dụng", job.title, "Từ chối tin");
            if (reason) run(function () { return V.api("/admin/jobs/" + job.id + "/reject", { method: "POST", body: { reason: reason } }); }, "Đã từ chối tin “" + job.title + "”.", load);
        }
        async function remove(job) {
            var reason = await reasonDialog("Gỡ tin vi phạm", job.title, "Gỡ tin");
            if (reason) run(function () { return V.api("/admin/jobs/" + job.id + "/remove", { method: "POST", body: { reason: reason } }); }, "Đã gỡ tin “" + job.title + "”.", load);
        }
        function detail(job) {
            V.modal(function (close) {
                var pending = job.status === "PENDING";
                return [
                    h("p", { class: "v-eyebrow", text: "Tin tuyển dụng" }), h("h2", { text: job.title }),
                    h("p", { class: "v-modal-sub" }, V.badge(V.JOB_STATUS, job.status), "  " + (job.company_name || "")),
                    job.status === "REJECTED" && h("div", { class: "v-note v-note-error", text: "Lý do từ chối: " + (job.reject_reason || "") }),
                    job.removed_at && h("div", { class: "v-note v-note-error", text: "Đã gỡ ngày " + V.date(job.removed_at) + ": " + (job.removal_reason || "") }),
                    h("dl", { class: "v-summary", style: "margin-top:0" },
                        kv("Ngành nghề", job.industry_name), kv("Địa điểm", [job.work_address, job.province_name].filter(Boolean).join(", ")),
                        kv("Mức lương", V.salary(job)), kv("Kinh nghiệm", V.EXPERIENCE[job.experience_level]), kv("Hình thức", V.EMPLOYMENT[job.employment_type]),
                        kv("Số lượng", String(job.positions)), kv("Hạn nộp", V.date(job.deadline))),
                    h("h3", { class: "v-card-title", text: "Mô tả công việc" }), V.prose(job.description),
                    h("h3", { class: "v-card-title v-mt-3", text: "Yêu cầu ứng viên" }), V.prose(job.requirements),
                    h("h3", { class: "v-card-title v-mt-3", text: "Quyền lợi" }), V.prose(job.benefits),
                    h("div", { class: "v-form-foot v-mt-3" }, h("span", {}), h("div", { class: "actions" },
                        pending && h("button", { type: "button", class: "v-btn v-btn-danger v-btn-sm", text: "Từ chối", onclick: function () { close(); reject(job); } }),
                        pending && h("button", { type: "button", class: "v-btn v-btn-primary v-btn-sm", text: "Duyệt tin", onclick: function () { close(); approve(job); } }),
                        !pending && h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Đóng", onclick: close })))
                ];
            }, { label: "Tin tuyển dụng " + job.title });
        }
        async function load() {
            V.loading(table);
            try {
                var data = await V.api("/admin/jobs", { query: { status: state.status, q: state.q, page: state.page, page_size: 10 } });
                V.clear(table);
                if (!data.items.length) return V.empty(table, state.status === "PENDING" ? "Không có tin tuyển dụng chờ duyệt" : "Không có tin phù hợp", "");
                table.appendChild(h("div", { class: "v-table-wrap" }, h("table", { class: "v-table" },
                    h("thead", {}, h("tr", {}, ["Tin tuyển dụng", "Công ty", "Hạn nộp", "Trạng thái", ""].map(function (t) { return h("th", { scope: "col", text: t }); }))),
                    h("tbody", {}, data.items.map(function (job) {
                        var pending = job.status === "PENDING", live = job.status === "APPROVED" && !job.removed_at;
                        return h("tr", {},
                            h("td", {}, h("strong", { text: job.title }), h("small", { text: [job.province_name, V.salary(job)].filter(Boolean).join(" · ") })),
                            h("td", { text: job.company_name || "—" }),
                            h("td", { class: "v-nowrap", text: V.date(job.deadline) }),
                            h("td", {}, job.removed_at ? h("span", { class: "v-badge v-badge-red", text: "Đã gỡ" }) : V.badge(V.JOB_STATUS, job.status),
                                (job.status === "REJECTED" || job.removed_at) && h("small", { style: "display:block;margin-top:6px;max-width:240px", text: "Lý do: " + (job.removed_at ? job.removal_reason : job.reject_reason || "") })),
                            h("td", {}, h("div", { class: "v-row-actions" },
                                h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", text: "Xem", "aria-label": "Xem tin " + job.title, onclick: function () { detail(job); } }),
                                pending && h("button", { type: "button", class: "v-btn v-btn-primary v-btn-xs", text: "Duyệt", "aria-label": "Duyệt tin " + job.title, onclick: function () { approve(job); } }),
                                pending && h("button", { type: "button", class: "v-btn v-btn-danger v-btn-xs", text: "Từ chối", "aria-label": "Từ chối tin " + job.title, onclick: function () { reject(job); } }),
                                live && h("button", { type: "button", class: "v-btn v-btn-danger v-btn-xs", text: "Gỡ tin", "aria-label": "Gỡ tin " + job.title, onclick: function () { remove(job); } }))));
                    })))));
                V.pagination(pager, data.page, data.total_pages, function (next) { state.page = next; load(); });
            } catch (error) { V.clear(pager); V.note(table, error.message, "error"); }
        }
        load();
    }

    function refreshCounters() {
        V.api("/admin/companies", { query: { status: "PENDING", page_size: 1 } }).then(function (d) { counters.companies.textContent = String(d.total); }).catch(function () {});
        V.api("/admin/jobs", { query: { status: "PENDING", page_size: 1 } }).then(function (d) { counters.jobs.textContent = String(d.total); }).catch(function () {});
        V.api("/admin/companies", { query: { status: "APPROVED", page_size: 1 } }).then(function (d) { counters.approvedCompanies.textContent = String(d.total); }).catch(function () {});
        V.api("/admin/jobs", { query: { status: "APPROVED", page_size: 1 } }).then(function (d) { counters.approvedJobs.textContent = String(d.total); }).catch(function () {});
    }
    function stat(key, iconName, label) {
        counters[key] = h("strong", { text: "–" });
        return h("div", { class: "v-stat v-stat-lg" }, V.icon(iconName, "v-icon-lg"), h("div", {}, h("small", { text: label }), counters[key]));
    }
    function route() {
        var tab = currentTab();
        V.note(message, "");
        tabsBox.querySelectorAll("a").forEach(function (link) { link.classList.toggle("is-active", link.dataset.tab === tab); link.setAttribute("aria-selected", String(link.dataset.tab === tab)); });
        if (tab === "jobs") renderJobs(); else renderCompanies();
    }

    async function init() {
        var user = await V.requireRole(["ADMIN"], app);
        if (!user) return;
        message = h("div", {});
        content = h("div", {});
        tabsBox = h("nav", { class: "v-tabs", "aria-label": "Mục quản trị" }, TABS.map(function (tab) { return h("a", { href: "#" + tab[0], "data-tab": tab[0], text: tab[1] }); }));
        V.clear(app);
        app.appendChild(h("section", { class: "v-page-head", style: "padding-bottom:0" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" }, h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }), h("span", { "aria-current": "page", text: "Quản trị" })),
            h("p", { class: "v-eyebrow", text: "Quản trị viên" }),
            h("h1", { class: "v-h1", text: "Kiểm duyệt nội dung" }),
            h("p", { class: "v-lead", text: "Duyệt hồ sơ công ty và tin tuyển dụng trước khi hiển thị công khai." }),
            h("div", { class: "v-stats" }, stat("companies", "brief", "Công ty chờ duyệt"), stat("jobs", "file", "Tin chờ duyệt"),
                stat("approvedCompanies", "shield", "Công ty đã duyệt"), stat("approvedJobs", "trend", "Tin đã duyệt")),
            tabsBox)));
        app.appendChild(h("section", { class: "v-section" }, h("div", { class: "v-wrap" }, message, content)));
        window.addEventListener("hashchange", route);
        refreshCounters();
        route();
    }
    init();
}());
