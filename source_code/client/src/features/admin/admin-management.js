(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var TYPES = { industries: "Ngành nghề", skills: "Kỹ năng", provinces: "Tỉnh/thành" };

    function button(text, action, danger) {
        return h("button", { type: "button", class: "v-btn v-btn-xs " + (danger ? "v-btn-danger" : "v-btn-outline"), text: text, onclick: action });
    }
    function table(headers, rows) {
        return h("div", { class: "v-table-wrap" }, h("table", { class: "v-table" },
            h("thead", {}, h("tr", {}, headers.map(function (name) { return h("th", { scope: "col", text: name }); }))),
            h("tbody", {}, rows)));
    }
    function field(label, input) { return h("label", { class: "v-field" }, h("span", { text: label }), input); }
    function select(label, options) {
        return h("select", { class: "v-input", "aria-label": label }, options.map(function (entry) { return h("option", { value: entry[0], text: entry[1] }); }));
    }
    function editor(title, fields, values, save, refresh) {
        V.modal(function (close) {
            var message = h("div", {});
            var submit = h("button", { type: "submit", class: "v-btn v-btn-primary v-btn-sm", text: "Lưu thay đổi" });
            var form = h("form", {}, h("h2", { text: title }), message, fields,
                h("div", { class: "v-form-foot" }, button("Hủy", close), submit));
            var busy = false;
            form.addEventListener("submit", async function (event) {
                event.preventDefault();
                if (busy || !form.reportValidity()) return;
                busy = true; submit.disabled = true;
                try {
                    await save(values());
                    close();
                    V.toast("Đã lưu thay đổi");
                    refresh();
                } catch (error) { V.note(message, error.message, "error"); }
                finally { busy = false; submit.disabled = false; }
            });
            return form;
        }, { label: title });
    }

    function users(container) {
        var state = { q: "", role: "", status: "", page: 1, page_size: 15 };
        var list = h("div", {}), pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang tài khoản" });
        var search = h("input", { class: "v-input", type: "search", placeholder: "Tên hoặc email", "aria-label": "Tìm tài khoản", maxlength: 100 });
        var role = select("Vai trò", [["", "Tất cả vai trò"], ["ADMIN", "Quản trị viên"], ["EMPLOYER", "Nhà tuyển dụng"], ["CANDIDATE", "Ứng viên"]]);
        var status = select("Trạng thái tài khoản", [["", "Tất cả trạng thái"], ["ACTIVE", "Hoạt động"], ["LOCKED", "Bị khóa"]]);
        var form = h("form", { class: "v-admin-toolbar" }, search, role, status, h("button", { type: "submit", class: "v-btn v-btn-primary v-btn-sm", text: "Tìm kiếm" }));
        V.clear(container).appendChild(h("div", {}, h("h2", { class: "v-h3", text: "Quản lý tài khoản" }), form, list, pager));
        var request = 0;
        async function detail(user) {
            try {
                var data = await V.api("/admin/users/" + user.id);
                V.modal(h("div", {}, h("h2", { text: data.full_name }),
                    h("p", { text: data.email }), h("p", { text: V.roleLabel(data.role) }),
                    h("p", { text: "Số điện thoại: " + (data.phone || "Chưa cập nhật") }),
                    h("p", { text: "Xác thực email: " + (data.is_email_verified ? "Đã xác thực" : "Chưa xác thực") }),
                    h("p", { text: "Đăng nhập gần nhất: " + V.date(data.last_login_at) }),
                    h("p", { text: "Số lần đăng nhập sai: " + data.failed_login_count })), { label: "Chi tiết tài khoản" });
            } catch (error) { V.toast(error.message, true); }
        }
        async function change(user, sourceButton) {
            if (sourceButton.disabled) return;
            sourceButton.disabled = true;
            var locked = user.status === "ACTIVE";
            try {
                if (!await V.confirm(locked ? "Khóa tài khoản" : "Mở khóa tài khoản", user.email, "Xác nhận", locked)) return;
                await V.api("/admin/users/" + user.id + "/status", { method: "PATCH", body: { status: locked ? "LOCKED" : "ACTIVE" } });
                V.toast(locked ? "Đã khóa tài khoản" : "Đã mở khóa tài khoản");
                await load();
            } catch (error) { V.toast(error.message, true); }
            finally { sourceButton.disabled = false; }
        }
        async function load() {
            var current = ++request;
            V.loading(list); V.clear(pager);
            try {
                var data = await V.api("/admin/users", { query: state });
                if (current !== request) return;
                V.clear(list);
                if (!data.items.length) return V.empty(list, "Không có tài khoản phù hợp", "");
                list.appendChild(table(["Tài khoản", "Vai trò", "Trạng thái", "Ngày tạo", "Thao tác"], data.items.map(function (user) {
                    var toggle = button(user.status === "ACTIVE" ? "Khóa" : "Mở khóa", function () { change(user, toggle); }, user.status === "ACTIVE");
                    return h("tr", {}, h("td", {}, h("strong", { text: user.full_name }), h("small", { text: user.email })),
                        h("td", { text: V.roleLabel(user.role) }), h("td", { text: user.status === "ACTIVE" ? "Hoạt động" : "Bị khóa" }),
                        h("td", { text: V.date(user.created_at) }), h("td", {}, h("div", { class: "v-row-actions" }, button("Xem", function () { detail(user); }), toggle)));
                })));
                V.pagination(pager, data.page, data.total_pages, function (next) { state.page = next; load(); });
            } catch (error) { if (current === request) V.note(list, error.message, "error"); }
        }
        form.addEventListener("submit", function (event) {
            event.preventDefault(); state.q = search.value.trim(); state.role = role.value; state.status = status.value; state.page = 1; load();
        });
        load();
    }

    function categories(container) {
        var data = {}, kind = "industries";
        var message = h("div", {}), list = h("div", {});
        var type = select("Loại danh mục", Object.keys(TYPES).map(function (key) { return [key, TYPES[key]]; }));
        var search = h("input", { class: "v-input", type: "search", placeholder: "Tìm tên danh mục", "aria-label": "Tìm danh mục" });
        V.clear(container).appendChild(h("div", {}, h("h2", { class: "v-h3", text: "Quản lý danh mục" }),
            h("div", { class: "v-admin-toolbar v-admin-toolbar-categories" }, type, search, button("Thêm danh mục", function () { edit(null); })), message, list));
        function edit(row) {
            var name = h("input", { class: "v-input", required: true, maxlength: 100, value: row ? row.name : "" });
            var code = h("input", { class: "v-input", required: true, maxlength: 10, value: row ? row.code : "" });
            var industry = select("Ngành nghề", [["", "Không gắn ngành"]].concat((data.industries || []).map(function (entry) { return [String(entry.id), entry.name + (entry.is_active ? "" : " (đã ẩn)")]; })));
            industry.value = row && row.industry_id ? String(row.industry_id) : "";
            var active = h("input", { type: "checkbox", checked: row ? row.is_active : true });
            var editingKind = kind;
            editor(row ? "Sửa danh mục" : "Thêm danh mục", [field("Tên", name),
                kind === "provinces" && field("Mã tỉnh/thành", code), kind === "skills" && field("Ngành nghề", industry),
                row && field("Đang hoạt động", active)], function () {
                var payload = { type: editingKind, name: name.value.trim() };
                if (editingKind === "provinces") payload.code = code.value.trim();
                if (editingKind === "skills") payload.industry_id = industry.value ? Number(industry.value) : null;
                if (row) payload.is_active = active.checked;
                return payload;
            }, function (payload) {
                return V.api("/admin/categories" + (row ? "/" + editingKind + "/" + row.id : ""), { method: row ? "PATCH" : "POST", body: payload });
            }, load);
        }
        function render() {
            V.clear(list);
            var query = search.value.trim().toLocaleLowerCase("vi-VN");
            var items = (data[kind] || []).filter(function (entry) { return entry.name.toLocaleLowerCase("vi-VN").includes(query); });
            if (!items.length) return V.empty(list, "Không có danh mục phù hợp", "");
            list.appendChild(table(["Tên", "Mã / ngành nghề", "Trạng thái", "Thao tác"], items.map(function (entry) {
                var industry = (data.industries || []).find(function (item) { return item.id === entry.industry_id; });
                return h("tr", {}, h("td", { text: entry.name }), h("td", { text: entry.code || entry.slug || (industry && industry.name) || "—" }),
                    h("td", { text: entry.is_active ? "Hoạt động" : "Đã ẩn" }), h("td", {}, button("Sửa / ẩn", function () { edit(entry); })));
            })));
        }
        async function load() {
            V.loading(list);
            try { data = await V.api("/admin/categories"); render(); }
            catch (error) { V.note(message, error.message, "error"); V.clear(list); }
        }
        type.addEventListener("change", function () { kind = type.value; render(); });
        search.addEventListener("input", render);
        load();
    }

    function pages(container) {
        async function load() {
            V.loading(container);
            try {
                var data = await V.api("/admin/pages");
                V.clear(container).appendChild(h("h2", { class: "v-h3", text: "Nội dung trang" }));
                if (!data.length) return V.empty(container, "Chưa có trang nội dung", "Chạy seed để tạo các trang giới thiệu, điều khoản và FAQ.");
                container.appendChild(table(["Trang", "Xuất bản", "Thao tác"], data.map(function (page) {
                    return h("tr", {}, h("td", { text: page.title }), h("td", { text: page.is_published ? "Đã xuất bản" : "Bản nháp" }), h("td", {},
                        button("Sửa", function () {
                            var title = h("input", { class: "v-input", value: page.title, required: true, maxlength: 200 });
                            var content = h("textarea", { rows: 12, required: true, maxlength: 50000, text: page.content });
                            var published = h("input", { type: "checkbox", checked: page.is_published });
                            editor("Sửa trang nội dung", [field("Tiêu đề", title), field("Nội dung", content), field("Xuất bản", published)],
                                function () { return { title: title.value.trim(), content: content.value.trim(), is_published: published.checked }; },
                                function (payload) { return V.api("/admin/pages/" + page.id, { method: "PATCH", body: payload }); }, load);
                        }), h("a", { class: "v-link", href: V.url("pages/content.html") + "?slug=" + encodeURIComponent(page.slug), text: "Xem trang" })));
                })));
            } catch (error) { V.note(container, error.message, "error"); }
        }
        load();
    }

    function audit(container) {
        var page = 1, list = h("div", {}), pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang nhật ký" });
        V.clear(container).appendChild(h("div", {}, h("h2", { class: "v-h3", text: "Nhật ký quản trị" }), list, pager));
        async function load() {
            V.loading(list); V.clear(pager);
            try {
                var data = await V.api("/admin/audit-logs", { query: { page: page, page_size: 20 } });
                V.clear(list);
                if (!data.items.length) return V.empty(list, "Chưa có nhật ký", "");
                list.appendChild(table(["Thời gian", "Người thực hiện", "Thao tác", "Đối tượng"], data.items.map(function (row) {
                    return h("tr", {}, h("td", { text: V.date(row.created_at) }), h("td", { text: row.actor_name || "Hệ thống" }),
                        h("td", { text: row.action }), h("td", { text: row.entity_type + " #" + row.entity_id }));
                })));
                V.pagination(pager, data.page, data.total_pages, function (next) { page = next; load(); });
            } catch (error) { V.note(list, error.message, "error"); }
        }
        load();
    }

    function settings(container) {
        async function load() {
            V.loading(container);
            try {
                var data = await V.api("/admin/upload-settings");
                V.clear(container).appendChild(h("h2", { class: "v-h3", text: "Giới hạn tải tệp" }));
                container.appendChild(table(["Cấu hình", "Giá trị", "Thao tác"], data.map(function (entry) {
                    return h("tr", {}, h("td", { text: entry.label }), h("td", { text: entry.value }), h("td", {}, button("Sửa", function () {
                        var input = h("input", { class: "v-input", value: entry.value, required: true, maxlength: 100 });
                        if (entry.key !== "cv_allowed_extensions") { input.type = "number"; input.min = "1"; input.step = "1"; }
                        editor("Sửa giới hạn tải tệp", field(entry.label, input), function () { return { value: input.value.trim() }; },
                            function (payload) { return V.api("/admin/upload-settings/" + entry.key, { method: "PATCH", body: payload }); }, load);
                    })));
                })));
            } catch (error) { V.note(container, error.message, "error"); }
        }
        load();
    }

    window.ViecoAdminManagement = { users: users, categories: categories, pages: pages, settings: settings, audit: audit };
}());
