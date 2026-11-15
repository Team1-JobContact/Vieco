/* Nhà tuyển dụng (PB-023): quản lý tin, danh sách ứng viên theo tin, xem hồ sơ/CV và cập nhật trạng thái đơn. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    var company = null;
    var body, message;
    var NEXT_LABEL = { VIEWED: "Đánh dấu đang xem xét", INTERVIEW: "Mời phỏng vấn", ACCEPTED: "Nhận ứng viên", REJECTED: "Từ chối" };

    function selectedJobId() { return new URLSearchParams(window.location.search).get("job_id"); }
    function go(jobId) {
        window.history.pushState(null, "", window.location.pathname + (jobId ? "?job_id=" + jobId : ""));
        route();
    }

    // ---------- Danh sách tin ----------
    function renderJobs() {
        var status = "", keyword = "", page = 1, timer = null;
        var list = h("div", {}), pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang" });
        var select = h("select", { "aria-label": "Lọc theo trạng thái tin" }, h("option", { value: "", text: "Tất cả" }),
            Object.keys(V.JOB_STATUS).map(function (key) { return h("option", { value: key, text: V.JOB_STATUS[key][0] }); }));
        var search = h("input", { class: "v-input", type: "search", placeholder: "Tìm theo tiêu đề tin", "aria-label": "Tìm theo tiêu đề tin", style: "height:44px;width:260px;max-width:100%" });
        V.clear(body);
        body.appendChild(h("div", { class: "v-results-head" },
            h("h2", { class: "v-h3", text: "Tin tuyển dụng của công ty" }),
            h("div", { class: "v-flex" }, search, h("label", { class: "v-select-inline" }, "Trạng thái:", select),
                h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/employer.html") + "#job" }, "Đăng tin mới", V.icon("plus")))));
        body.appendChild(list);
        body.appendChild(pager);

        async function act(job, path, confirmText, options) {
            options = options || {};
            if (confirmText && !(await V.confirm(confirmText[0], confirmText[1], confirmText[2], options.danger))) return;
            try {
                await V.api("/employer/jobs/" + job.id + path, { method: options.method || "POST", body: options.body });
                V.note(message, options.done || "Đã cập nhật tin tuyển dụng.", "success");
                load();
            } catch (error) { V.note(message, error.message, "error"); }
        }
        function extend(job) {
            V.modal(function (close) {
                var input = h("input", { type: "date", required: true, min: new Date().toISOString().slice(0, 10), value: job.deadline || "" });
                var error = h("div", {});
                var form = h("form", {}, h("p", { class: "v-eyebrow", text: "Gia hạn tin" }), h("h2", { text: job.title }),
                    h("p", { class: "v-modal-sub", text: "Hạn nộp hiện tại: " + V.date(job.deadline) }), error,
                    h("label", { class: "v-field" }, h("span", { text: "Hạn nộp hồ sơ mới" }), input),
                    h("div", { class: "v-form-foot" }, h("span", {}), h("div", { class: "actions" },
                        h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Hủy", onclick: close }),
                        h("button", { type: "submit", class: "v-btn v-btn-primary v-btn-sm", text: "Gia hạn" }))));
                form.addEventListener("submit", async function (event) {
                    event.preventDefault();
                    if (!input.value) return V.note(error, "Vui lòng chọn hạn nộp mới.", "error");
                    try {
                        await V.api("/employer/jobs/" + job.id + "/extend", { method: "POST", body: { deadline: input.value } });
                        close();
                        V.note(message, "Đã gia hạn tin tuyển dụng.", "success");
                        load();
                    } catch (e) { V.note(error, e.message, "error"); }
                });
                return form;
            }, { label: "Gia hạn tin" });
        }
        function actions(job) {
            var editable = job.status === "DRAFT" || job.status === "REJECTED";
            function btn(label, handler, cls) { return h("button", { type: "button", class: "v-btn v-btn-xs " + (cls || "v-btn-outline"), text: label, onclick: handler }); }
            return h("div", { class: "v-row-actions" },
                h("button", { type: "button", class: "v-btn v-btn-primary v-btn-xs", onclick: function () { go(job.id); } }, V.icon("users", "v-icon-sm"), "Ứng viên (" + job.application_count + ")"),
                editable && h("a", { class: "v-btn v-btn-outline v-btn-xs", href: V.url("pages/employer.html") + "?job_id=" + job.id + "#job", text: "Sửa" }),
                editable && btn("Gửi duyệt", function () { act(job, "/submit", null, { done: "Đã gửi tin cho Admin duyệt." }); }),
                job.status === "APPROVED" && btn("Đóng tin", function () { act(job, "/close", ["Đóng tin tuyển dụng?", "Tin sẽ ngừng hiển thị và không nhận đơn mới. Các đơn đã nộp vẫn được giữ.", "Đóng tin"]); }),
                job.status === "CLOSED" && btn("Mở lại", function () { act(job, "/reopen", null, { done: "Đã mở lại tin tuyển dụng." }); }),
                (job.status === "APPROVED" || job.status === "EXPIRED" || job.status === "CLOSED") && btn("Gia hạn", function () { extend(job); }),
                job.status === "DRAFT" && btn("Xóa", function () { act(job, "", ["Xóa tin nháp?", "Tin nháp “" + job.title + "” sẽ bị xóa vĩnh viễn.", "Xóa tin"], { method: "DELETE", danger: true, done: "Đã xóa tin nháp." }); }, "v-btn-danger"));
        }
        async function load() {
            V.loading(list);
            try {
                var data = await V.api("/employer/jobs", { query: { status: status, q: keyword, page: page, page_size: 10 } });
                V.clear(list);
                if (!data.items.length) {
                    return V.empty(list, status || keyword ? "Không có tin phù hợp" : "Công ty chưa có tin tuyển dụng", "Tạo tin đầu tiên để bắt đầu nhận hồ sơ ứng viên.",
                        h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/employer.html") + "#job", text: "Đăng tin mới" }));
                }
                data.items.forEach(function (job) {
                    list.appendChild(h("article", { class: "v-row", style: "grid-template-columns:minmax(0,1.5fr) minmax(0,.7fr) auto;align-items:start" },
                        h("div", {}, h("h3", { text: job.title }),
                            h("p", { class: "sub", text: [job.province_name, V.salary(job), V.EMPLOYMENT[job.employment_type]].filter(Boolean).join(" · ") }),
                            job.status === "REJECTED" && job.reject_reason && h("p", { class: "v-small", style: "color:var(--v-danger);margin-top:6px", text: "Lý do từ chối: " + job.reject_reason }),
                            job.removed_at && h("p", { class: "v-small", style: "color:var(--v-danger);margin-top:6px", text: "Tin đã bị gỡ: " + (job.removal_reason || "") })),
                        h("div", {}, V.badge(V.JOB_STATUS, job.status), h("small", { style: "margin-top:8px", text: "Hạn nộp: " + V.date(job.deadline) + " · " + job.view_count + " lượt xem" })),
                        actions(job)));
                });
                V.pagination(pager, data.page, data.total_pages, function (next) { page = next; load(); });
            } catch (error) { V.clear(pager); V.note(list, error.message, "error"); }
        }
        select.addEventListener("change", function () { status = select.value; page = 1; load(); });
        search.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { keyword = search.value.trim(); page = 1; load(); }, 300); });
        load();
    }

    // ---------- Ứng viên của một tin ----------
    async function renderApplicants(jobId) {
        var job;
        V.loading(body);
        try { job = await V.api("/employer/jobs/" + encodeURIComponent(jobId)); }
        catch (error) {
            V.clear(body);
            body.appendChild(h("button", { type: "button", class: "v-link v-mb-2", text: "← Tất cả tin tuyển dụng", onclick: function () { go(null); } }));
            var box = h("div", {});
            body.appendChild(box);
            return V.note(box, error.message, "error");
        }
        var status = "", page = 1;
        var list = h("div", {}), pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang" });
        var select = h("select", { "aria-label": "Lọc theo trạng thái đơn" }, h("option", { value: "", text: "Tất cả" }),
            Object.keys(V.APP_STATUS).map(function (key) { return h("option", { value: key, text: V.APP_STATUS[key][0] }); }));
        V.clear(body);
        body.appendChild(h("button", { type: "button", class: "v-link v-mb-2", text: "← Tất cả tin tuyển dụng", onclick: function () { go(null); } }));
        body.appendChild(h("div", { class: "v-results-head" },
            h("div", {}, h("h2", { class: "v-h3", text: "Ứng viên: " + job.title }),
                h("p", { class: "v-flex v-small v-muted", style: "margin-top:6px" }, V.badge(V.JOB_STATUS, job.status), "Hạn nộp " + V.date(job.deadline) + " · " + job.application_count + " đơn")),
            h("label", { class: "v-select-inline" }, "Trạng thái:", select)));
        body.appendChild(list);
        body.appendChild(pager);

        async function load() {
            V.loading(list);
            try {
                var data = await V.api("/employer/jobs/" + job.id + "/applications", { query: { status: status, page: page, page_size: 10 } });
                V.clear(list);
                if (!data.items.length) return V.empty(list, status ? "Không có đơn ở trạng thái này" : "Tin này chưa có ứng viên", "Đơn ứng tuyển mới sẽ xuất hiện tại đây và bạn sẽ nhận được thông báo.");
                data.items.forEach(function (item) {
                    list.appendChild(h("article", { class: "v-row" },
                        h("span", { class: "v-logo v-logo-sm", style: "border-radius:50%;background:var(--v-blue);color:var(--v-gold);border:0", text: V.initials(item.candidate_name) }),
                        h("div", {}, h("h3", { text: item.candidate_name || "Ứng viên" }),
                            h("p", { class: "sub", text: [item.candidate_headline, item.candidate_email, item.candidate_phone].filter(Boolean).join(" · ") })),
                        h("div", {}, h("small", { text: "Ngày nộp" }), V.date(item.created_at)),
                        V.badge(V.APP_STATUS, item.status),
                        h("button", { type: "button", class: "v-link", text: "Xem hồ sơ ↗", onclick: function () { openApplicant(item.id, load); } })));
                });
                V.pagination(pager, data.page, Math.ceil(data.total / data.page_size), function (next) { page = next; load(); });
            } catch (error) { V.clear(pager); V.note(list, error.message, "error"); }
        }
        select.addEventListener("change", function () { status = select.value; page = 1; load(); });
        load();
    }

    async function openApplicant(id, onChanged) {
        var detail;
        try { detail = await V.api("/applications/" + id); } catch (error) { return V.toast(error.message, true); }
        // Mở đơn mới coi như đã xem: tự chuyển NEW -> VIEWED để ứng viên biết hồ sơ đã được đọc.
        if (detail.status === "NEW") {
            try {
                await V.api("/applications/" + id + "/status", { method: "PATCH", body: { status: "VIEWED" } });
                detail = await V.api("/applications/" + id);
                if (onChanged) onChanged();
            } catch (_) { /* vẫn hiển thị hồ sơ nếu không đổi được trạng thái */ }
        }
        var p = detail.candidate_profile || {};
        function kv(label, value) { return h("div", { class: "v-kv" }, h("dt", { text: label }), h("dd", { text: value || "—" })); }
        V.modal(function (close) {
            var error = h("div", {});
            var noteInput = h("textarea", { rows: 2, maxlength: 500, placeholder: "Ghi chú cho lần cập nhật này (không bắt buộc)" });
            var buttons = detail.allowed_statuses.map(function (next) {
                var button = h("button", { type: "button", class: "v-btn v-btn-sm " + (next === "REJECTED" ? "v-btn-danger" : next === "VIEWED" ? "v-btn-outline" : "v-btn-primary"), text: NEXT_LABEL[next] });
                button.addEventListener("click", async function () {
                    if (next === "REJECTED" && !(await V.confirm("Từ chối ứng viên này?", "Trạng thái từ chối là kết quả cuối, không thể thay đổi sau đó.", "Từ chối", true))) return;
                    if (next === "ACCEPTED" && !(await V.confirm("Nhận ứng viên này?", "Trạng thái trúng tuyển là kết quả cuối, không thể thay đổi sau đó.", "Nhận ứng viên"))) return;
                    try {
                        await V.api("/applications/" + id + "/status", { method: "PATCH", body: { status: next, note: noteInput.value.trim() || null } });
                        close();
                        V.toast("Đã cập nhật trạng thái đơn. Ứng viên sẽ nhận được thông báo.");
                        if (onChanged) onChanged();
                    } catch (e) { V.note(error, e.message, "error"); }
                });
                return button;
            });
            return [
                h("p", { class: "v-eyebrow", text: "Hồ sơ ứng viên" }),
                h("h2", { text: detail.candidate_name }),
                h("p", { class: "v-modal-sub", text: [detail.candidate_headline, "Ứng tuyển " + detail.job_title, "Nộp ngày " + V.date(detail.created_at)].filter(Boolean).join("  ·  ") }),
                error,
                h("div", { class: "v-flex v-between v-mb-3" }, V.badge(V.APP_STATUS, detail.status),
                    h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", onclick: function () {
                        V.download("/applications/" + id + "/cv", detail.cv_file_name).catch(function (e) { V.note(error, e.message, "error"); });
                    } }, V.icon("download", "v-icon-sm"), "Tải CV: " + (detail.cv_file_name || "CV"))),
                h("dl", { class: "v-summary", style: "margin-top:0" },
                    kv("Email", detail.candidate_email), kv("Số điện thoại", detail.candidate_phone),
                    kv("Ngày sinh", p.date_of_birth ? V.date(p.date_of_birth) : null), kv("Nơi ở", [p.address, p.province_name].filter(Boolean).join(", "))),
                p.summary && h("div", { class: "v-card v-mb-3" }, h("h3", { class: "v-card-title", text: "Giới thiệu bản thân" }), h("p", { class: "v-small", style: "white-space:pre-wrap", text: p.summary })),
                detail.cover_letter && h("div", { class: "v-card v-mb-3" }, h("h3", { class: "v-card-title", text: "Thư giới thiệu" }), h("p", { class: "v-small", style: "white-space:pre-wrap", text: detail.cover_letter })),
                h("h3", { class: "v-card-title v-mt-3", text: "Lịch sử xử lý" }),
                h("ol", { class: "v-timeline" }, detail.history.map(function (step) {
                    return h("li", {}, h("strong", { text: V.APP_STATUS[step.to_status][0] }), step.note && h("span", { text: " — " + step.note }),
                        h("small", { text: [V.date(step.created_at), step.changed_by_name].filter(Boolean).join(" · ") }));
                })),
                buttons.length ? h("div", { class: "v-mt-3" }, h("label", { class: "v-field" }, h("span", { text: "Cập nhật trạng thái đơn" }), noteInput),
                    h("div", { class: "v-flex", style: "justify-content:flex-end" }, buttons))
                    : h("p", { class: "v-small v-muted v-mt-3", text: "Đơn đã ở trạng thái cuối, không thể cập nhật thêm." })
            ];
        }, { label: "Hồ sơ ứng viên" });
    }

    function route() {
        V.note(message, "");
        var jobId = selectedJobId();
        if (jobId) renderApplicants(jobId); else renderJobs();
    }

    async function init() {
        var user = await V.requireRole(["EMPLOYER"], app);
        if (!user) return;
        var gate = null;
        try { company = await V.api("/employer/company"); }
        catch (error) {
            if (error.status !== 404) {
                var wrap = h("div", { class: "v-wrap v-section" });
                V.clear(app).appendChild(wrap);
                return V.note(wrap, error.message, "error");
            }
        }
        if (!company) gate = ["Bạn chưa có hồ sơ công ty", "Tạo hồ sơ công ty và gửi Admin duyệt để bắt đầu đăng tin tuyển dụng.", "Tạo hồ sơ công ty"];
        else if (company.status === "PENDING") gate = ["Hồ sơ công ty đang chờ duyệt", "Admin sẽ xem xét hồ sơ. Bạn sẽ nhận được thông báo khi có kết quả.", "Xem hồ sơ công ty"];
        else if (company.status === "REJECTED") gate = ["Hồ sơ công ty bị từ chối", "Lý do: " + (company.reject_reason || "chưa có") + ". Hãy cập nhật và gửi duyệt lại.", "Cập nhật hồ sơ công ty"];

        message = h("div", {});
        body = h("div", {});
        V.clear(app);
        app.appendChild(h("section", { class: "v-page-head" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" }, h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }), h("span", { "aria-current": "page", text: "Quản lý tuyển dụng" })),
            h("div", { class: "v-title-row" },
                company ? V.logo(company.name) : null,
                h("div", { class: "grow" }, h("p", { class: "v-eyebrow", text: "Nhà tuyển dụng" }),
                    h("h1", { text: company ? company.name : "Quản lý tuyển dụng" }),
                    company && h("div", { class: "v-meta" }, V.badge(V.COMPANY_STATUS, company.status), h("span", { text: company.member_role === "OWNER" ? "Chủ sở hữu" : "Thành viên" }))),
                h("div", { class: "v-title-actions" },
                    h("a", { class: "v-btn v-btn-outline", href: V.url("pages/employer.html") }, "Hồ sơ công ty", V.icon("edit")),
                    company && company.status === "APPROVED" && h("a", { class: "v-btn v-btn-primary", href: V.companyUrl(company.id) }, "Xem trang công ty", V.icon("out")))))));
        var wrapMain = h("div", { class: "v-wrap" }, message, body);
        app.appendChild(h("section", { class: "v-section" }, wrapMain));
        if (gate) {
            return V.empty(body, gate[0], gate[1], h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/employer.html"), text: gate[2] }));
        }
        window.addEventListener("popstate", route);
        route();
    }
    init();
}());
