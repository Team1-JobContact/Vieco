/* Hồ sơ của tôi (PB-021, PB-022): tổng quan, đơn đã ứng tuyển + rút đơn, việc đã lưu, CV, thông báo, cài đặt. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    var TABS = [["overview", "Tổng quan"], ["history", "Học vấn & kinh nghiệm"], ["applications", "Việc đã ứng tuyển"], ["saved", "Việc đã lưu"], ["cvs", "CV của tôi"], ["notifications", "Thông báo"], ["settings", "Cài đặt tài khoản"]];
    var GENDERS = { MALE: "Nam", FEMALE: "Nữ", OTHER: "Khác" };
    var user, profile = null, cvData = { items: [], total: 0, max_count: 5, max_size_mb: 5, allowed_extensions: ["pdf", "doc", "docx"] };
    var counts = { applications: 0, saved: 0, unread: 0 };
    var content, sideCv, headBox, tabsBox, statNodes = {};

    function currentTab() {
        var hash = window.location.hash.replace("#", "");
        return TABS.some(function (t) { return t[0] === hash; }) ? hash : "overview";
    }
    function stat(key, iconName, label) {
        statNodes[key] = h("strong", { text: "0" });
        return h("div", { class: "v-stat v-stat-lg" }, V.icon(iconName, "v-icon-lg"), h("div", {}, h("small", { text: label }), statNodes[key]));
    }
    function paintCounts() {
        statNodes.applications.textContent = String(counts.applications);
        statNodes.saved.textContent = String(counts.saved);
        statNodes.cvs.textContent = String(cvData.total);
        statNodes.unread.textContent = String(counts.unread);
        tabsBox.querySelectorAll("a").forEach(function (link) {
            var key = link.dataset.tab, n = { applications: counts.applications, saved: counts.saved }[key];
            link.textContent = link.dataset.label + (n !== undefined ? " (" + n + ")" : "");
        });
    }

    function renderHead() {
        V.clear(headBox);
        headBox.appendChild(h("div", { class: "v-title-row" },
            h("span", { class: "v-avatar", style: "overflow:hidden" }, V.media(user.avatar_url)
                ? h("img", { src: V.media(user.avatar_url), alt: "Ảnh đại diện", style: "width:100%;height:100%;object-fit:cover" })
                : V.initials(user.full_name)),
            h("div", { class: "grow" },
                h("p", { class: "v-eyebrow", text: "Ứng viên" }),
                h("h1", { text: user.full_name }),
                h("div", { class: "v-meta" },
                    h("span", { class: "strong", text: (profile && profile.headline) || "Chưa cập nhật chức danh mong muốn" }),
                    profile && profile.province_name && h("span", {}, V.icon("pin", "v-icon-sm"), profile.province_name),
                    h("span", {}, V.icon("mail", "v-icon-sm"), user.email))),
            h("div", { class: "v-title-actions" },
                h("a", { class: "v-btn v-btn-outline", href: "#settings" }, "Chỉnh sửa hồ sơ", V.icon("edit")),
                h("a", { class: "v-btn v-btn-primary", href: V.url("pages/jobs.html") }, "Tìm việc ngay", V.icon("out")))));
    }

    // ---------- Đơn ứng tuyển ----------
    function applicationRow(item, onChanged) {
        return h("article", { class: "v-row" },
            V.logo(item.company_name, "v-logo-sm", item.company_logo_url),
            h("div", {}, h("h3", {}, h("a", { href: V.jobUrl(item.job_id), text: item.job_title || "Tin tuyển dụng" })), h("p", { class: "sub", text: item.company_name || "" })),
            h("div", {}, h("small", { text: "Ngày nộp" }), V.date(item.created_at)),
            V.badge(V.APP_STATUS, item.status),
            h("button", { type: "button", class: "v-link", text: "Xem chi tiết ↗", onclick: function () { openApplication(item.id, onChanged); } }));
    }

    async function openApplication(id, onChanged) {
        var detail;
        try { detail = await V.api("/applications/" + id); } catch (error) { return V.toast(error.message, true); }
        V.modal(function (close) {
            var message = h("div", {});
            var withdraw = detail.can_withdraw ? h("button", { type: "button", class: "v-btn v-btn-danger v-btn-sm", text: "Rút đơn ứng tuyển" }) : null;
            if (withdraw) withdraw.addEventListener("click", async function () {
                if (!(await V.confirm("Rút đơn ứng tuyển?", "Sau khi rút, bạn không thể nộp lại đơn cho tin này.", "Rút đơn", true))) return;
                withdraw.disabled = true;
                try {
                    await V.api("/applications/" + id + "/withdraw", { method: "PATCH" });
                    close();
                    V.toast("Đã rút đơn ứng tuyển");
                    if (onChanged) onChanged();
                } catch (error) { V.note(message, error.message, "error"); withdraw.disabled = false; }
            });
            return [
                h("p", { class: "v-eyebrow", text: "Đơn ứng tuyển" }),
                h("h2", { text: detail.job_title }),
                h("p", { class: "v-modal-sub", text: [detail.company_name, detail.province_name, "Nộp ngày " + V.date(detail.created_at)].filter(Boolean).join("  ·  ") }),
                message,
                h("div", { class: "v-flex v-between v-mb-3" }, V.badge(V.APP_STATUS, detail.status),
                    h("button", { type: "button", class: "v-link", onclick: function () {
                        V.download("/applications/" + id + "/cv", detail.cv_file_name).catch(function (e) { V.toast(e.message, true); });
                    } }, "Tải CV đã nộp: " + (detail.cv_file_name || "CV"))),
                detail.cover_letter && h("div", { class: "v-card v-mb-3" }, h("h3", { class: "v-card-title", text: "Thư giới thiệu" }),
                    h("p", { class: "v-small", style: "white-space:pre-wrap", text: detail.cover_letter })),
                h("h3", { class: "v-card-title", text: "Lịch sử trạng thái" }),
                h("ol", { class: "v-timeline" }, detail.history.map(function (step) {
                    return h("li", {}, h("strong", { text: V.APP_STATUS[step.to_status][0] }), step.note && h("span", { text: " — " + step.note }),
                        h("small", { text: V.date(step.created_at) + " · " + V.ago(step.created_at) }));
                })),
                h("div", { class: "v-form-foot v-mt-3" },
                    h("p", { class: "v-small v-muted", text: detail.can_withdraw ? "Bạn có thể rút đơn khi nhà tuyển dụng chưa mời phỏng vấn." : "" }),
                    h("div", { class: "actions" }, withdraw, h("a", { class: "v-btn v-btn-outline v-btn-sm", href: V.jobUrl(detail.job_id), text: "Xem tin tuyển dụng" })))
            ];
        }, { label: "Chi tiết đơn ứng tuyển" });
    }

    function renderApplications(box, limit) {
        var status = "", page = 1;
        var list = h("div", {}), pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang" });
        var select = h("select", { "aria-label": "Lọc theo trạng thái" }, h("option", { value: "", text: "Tất cả" }),
            Object.keys(V.APP_STATUS).map(function (key) { return h("option", { value: key, text: V.APP_STATUS[key][0] }); }));
        box.appendChild(h("div", { class: "v-results-head" }, h("h2", { class: "v-h3", text: limit ? "Đơn ứng tuyển gần đây" : "Việc đã ứng tuyển" }),
            limit ? h("a", { class: "v-link", href: "#applications", text: "Xem tất cả ↗" }) : h("label", { class: "v-select-inline" }, "Trạng thái:", select)));
        box.appendChild(list);
        if (!limit) box.appendChild(pager);
        async function load() {
            V.loading(list);
            try {
                var data = await V.api("/applications/my-applications", { query: { status: status, page: page, page_size: limit || 8 } });
                if (!status) { counts.applications = data.total; paintCounts(); }
                V.clear(list);
                if (!data.items.length) {
                    return V.empty(list, status ? "Không có đơn ở trạng thái này" : "Bạn chưa ứng tuyển việc làm nào", "Khám phá các vị trí đang tuyển và gửi hồ sơ chỉ trong vài phút.",
                        h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/jobs.html"), text: "Tìm việc ngay" }));
                }
                data.items.forEach(function (item) { list.appendChild(applicationRow(item, load)); });
                if (data.items.some(function (item) { return item.status === "INTERVIEW"; })) {
                    list.appendChild(h("div", { class: "v-banner v-mt-2" }, h("div", { class: "v-flex" }, V.icon("clock", "v-icon-lg"),
                        h("div", {}, h("h3", { text: "Bạn có lời mời phỏng vấn" }), h("p", { text: "Nhà tuyển dụng sẽ liên hệ qua email hoặc số điện thoại trong hồ sơ của bạn." })))));
                }
                if (!limit) V.pagination(pager, data.page, Math.ceil(data.total / data.page_size), function (next) { page = next; load(); });
            } catch (error) { V.note(list, error.message, "error"); }
        }
        select.addEventListener("change", function () { status = select.value; page = 1; load(); });
        load();
    }

    // ---------- Việc đã lưu ----------
    async function renderSaved(box) {
        box.appendChild(h("h2", { class: "v-h3 v-mb-2", text: "Việc đã lưu" }));
        var list = h("div", {});
        box.appendChild(list);
        V.loading(list);
        try {
            var data = await V.api("/saved-jobs");
            counts.saved = data.total;
            paintCounts();
            V.clear(list);
            if (!data.items.length) {
                return V.empty(list, "Bạn chưa lưu việc làm nào", "Bấm biểu tượng đánh dấu trên tin tuyển dụng để lưu lại và xem sau.",
                    h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/jobs.html"), text: "Khám phá việc làm" }));
            }
            data.items.forEach(function (job) { list.appendChild(V.jobRow(job)); });
        } catch (error) { V.note(list, error.message, "error"); }
    }

    // ---------- CV ----------
    async function refreshCvs() {
        cvData = await V.api("/candidates/me/cvs");
        paintCounts();
        renderSideCv();
    }
    function uploadControl(onDone, messageBox) {
        var input = h("input", { type: "file", hidden: true, accept: "." + cvData.allowed_extensions.join(",.") });
        var button = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm v-btn-block" }, "Tải CV mới", V.icon("plus"));
        button.addEventListener("click", function () {
            if (cvData.total >= cvData.max_count) return V.note(messageBox, "Bạn đã có tối đa " + cvData.max_count + " CV. Hãy xóa bớt CV cũ trước khi tải lên.", "warn");
            input.click();
        });
        input.addEventListener("change", async function () {
            var file = input.files[0];
            if (!file) return;
            var ext = file.name.split(".").pop().toLowerCase();
            input.value = "";
            if (cvData.allowed_extensions.indexOf(ext) === -1) return V.note(messageBox, "Chỉ chấp nhận tệp " + cvData.allowed_extensions.join(", ").toUpperCase() + ".", "error");
            if (file.size > cvData.max_size_mb * 1024 * 1024) return V.note(messageBox, "Tệp CV vượt quá " + cvData.max_size_mb + "MB.", "error");
            button.disabled = true;
            V.note(messageBox, "Đang tải CV lên...");
            try {
                var data = new FormData();
                data.append("file", file);
                await V.api("/candidates/me/cvs", { method: "POST", formData: data });
                await refreshCvs();
                V.note(messageBox, "Đã tải CV lên thành công.", "success");
                if (onDone) onDone();
            } catch (error) { V.note(messageBox, error.message, "error"); }
            button.disabled = false;
        });
        return [button, input];
    }
    function renderCvs(box) {
        var message = h("div", {}), list = h("div", {});
        box.appendChild(h("div", { class: "v-results-head" }, h("h2", { class: "v-h3", text: "CV của tôi" }),
            h("span", { class: "v-muted v-small", text: cvData.allowed_extensions.join(", ").toUpperCase() + " · tối đa " + cvData.max_size_mb + "MB mỗi tệp · tối đa " + cvData.max_count + " CV" })));
        box.appendChild(message);
        box.appendChild(list);
        function paint() {
            V.clear(list);
            if (!cvData.items.length) V.empty(list, "Bạn chưa có CV nào", "Tải CV lên để sẵn sàng ứng tuyển chỉ với một lần bấm.");
            cvData.items.forEach(function (cv) {
                var actions = h("div", { class: "v-row-actions" },
                    h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", "aria-label": "Tải xuống " + cv.file_name, onclick: function () {
                        V.download("/candidates/me/cvs/" + cv.id + "/download", cv.file_name).catch(function (e) { V.note(message, e.message, "error"); });
                    } }, V.icon("download", "v-icon-sm"), "Tải xuống"),
                    !cv.is_default && h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", text: "Đặt mặc định", onclick: async function () {
                        try { await V.api("/candidates/me/cvs/" + cv.id + "/default", { method: "PATCH" }); await refreshCvs(); paint(); V.note(message, "Đã đặt CV mặc định.", "success"); }
                        catch (error) { V.note(message, error.message, "error"); }
                    } }),
                    h("button", { type: "button", class: "v-btn v-btn-danger v-btn-xs", "aria-label": "Xóa " + cv.file_name, onclick: async function () {
                        if (!(await V.confirm("Xóa CV này?", "“" + cv.file_name + "” sẽ bị xóa khỏi hồ sơ. Đơn đã nộp bằng CV này vẫn giữ nguyên.", "Xóa CV", true))) return;
                        try { await V.api("/candidates/me/cvs/" + cv.id, { method: "DELETE" }); await refreshCvs(); paint(); V.note(message, "Đã xóa CV.", "success"); }
                        catch (error) { V.note(message, error.message, "error"); }
                    } }, V.icon("trash", "v-icon-sm"), "Xóa"));
                list.appendChild(h("article", { class: "v-row", style: "grid-template-columns:52px minmax(0,1fr) auto auto" },
                    h("span", { class: "v-logo v-logo-sm", style: "color:var(--v-blue)" }, V.icon("file", "v-icon-lg")),
                    h("div", {}, h("h3", { text: cv.file_name }), h("p", { class: "sub", text: Math.max(1, Math.round(cv.file_size / 1024)) + " KB · tải lên " + V.ago(cv.created_at).toLowerCase() })),
                    cv.is_default ? h("span", { class: "v-badge v-badge-sand", text: "Mặc định" }) : h("span", {}),
                    actions));
            });
            list.appendChild(h("div", { class: "v-mt-3", style: "max-width:320px" }, uploadControl(paint, message)));
        }
        paint();
    }
    function renderSideCv() {
        if (!sideCv) return;
        V.clear(sideCv);
        var message = h("div", {});
        var main = cvData.items.filter(function (cv) { return cv.is_default; })[0] || cvData.items[0];
        sideCv.appendChild(h("h2", { class: "v-card-title" }, "CV của tôi", h("a", { class: "v-link v-small", href: "#cvs", text: "Quản lý ↗" })));
        sideCv.appendChild(main ? h("div", { class: "v-flex v-mb-2", style: "flex-wrap:nowrap" },
            h("span", { class: "v-logo v-logo-md", style: "color:var(--v-blue);background:var(--v-bg)" }, V.icon("file", "v-icon-lg")),
            h("div", { style: "min-width:0" }, h("strong", { style: "font-weight:500;overflow-wrap:anywhere", text: main.file_name }),
                h("p", { class: "v-small v-muted", text: "Cập nhật " + V.ago(main.created_at).toLowerCase() }),
                h("p", { class: "v-small", style: "color:var(--v-gold-ink)", text: "Đang dùng để ứng tuyển" })))
            : h("p", { class: "v-small v-muted v-mb-2", text: "Bạn chưa có CV. Tải CV lên để bắt đầu ứng tuyển." }));
        sideCv.appendChild(message);
        uploadControl(function () { if (currentTab() === "cvs") renderTab(); }, message).forEach(function (node) { sideCv.appendChild(node); });
    }

    // ---------- Cài đặt ----------
    function renderSettings(box) {
        var message = h("div", {});
        var p = profile || {};
        function field(label, control) { return h("label", { class: "v-field" }, h("span", { text: label }), control); }
        var fullName = h("input", { type: "text", name: "full_name", value: user.full_name || "", required: true, maxlength: 150 });
        var phone = h("input", { type: "tel", name: "phone", value: user.phone || "", placeholder: "0901234567" });
        var dob = h("input", { type: "date", name: "date_of_birth", value: p.date_of_birth || "" });
        var gender = h("select", { name: "gender" }, h("option", { value: "", text: "Không chọn" }),
            Object.keys(GENDERS).map(function (key) { return h("option", { value: key, text: GENDERS[key], selected: p.gender === key }); }));
        var province = h("select", { name: "province_id" }, h("option", { value: "", text: "Chọn tỉnh/thành" }));
        var address = h("input", { type: "text", name: "address", value: p.address || "", maxlength: 255 });
        var headline = h("input", { type: "text", name: "headline", value: p.headline || "", maxlength: 150, placeholder: "Ví dụ: Marketing Specialist" });
        var summary = h("textarea", { name: "summary", rows: 5, maxlength: 5000, placeholder: "Giới thiệu ngắn về kinh nghiệm và mục tiêu nghề nghiệp của bạn" });
        summary.value = p.summary || "";
        var visibility = h("select", { name: "visibility" },
            h("option", { value: "PUBLIC", text: "Công khai – nhà tuyển dụng có thể xem", selected: p.visibility !== "PRIVATE" }),
            h("option", { value: "PRIVATE", text: "Riêng tư – chỉ công ty bạn ứng tuyển xem được", selected: p.visibility === "PRIVATE" }));
        V.categories().then(function (data) { V.fillSelect(province, data.provinces, "Chọn tỉnh/thành"); province.value = p.province_id ? String(p.province_id) : ""; });
        var submit = h("button", { type: "submit", class: "v-btn v-btn-primary v-btn-sm", text: "Lưu thay đổi" });
        var form = h("form", { class: "v-card", novalidate: true },
            h("h2", { class: "v-h3 v-mb-3", text: "Thông tin hồ sơ" }), message,
            h("div", { class: "v-field-row" }, field("Họ và tên", fullName), field("Số điện thoại", phone)),
            field("Email đăng nhập", h("input", { type: "email", value: user.email, disabled: true })),
            h("div", { class: "v-field-row" }, field("Ngày sinh", dob), field("Giới tính", gender)),
            h("div", { class: "v-field-row" }, field("Tỉnh/thành", province), field("Địa chỉ", address)),
            field("Chức danh mong muốn", headline), field("Giới thiệu bản thân", summary), field("Chế độ hiển thị hồ sơ", visibility),
            h("div", { class: "v-form-foot" }, h("span", {}), h("div", { class: "actions" }, submit)));
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            if (submit.disabled) return;
            if (fullName.value.trim().length < 2) return V.note(message, "Họ tên phải từ 2 đến 150 ký tự.", "error");
            if (phone.value.trim() && !/^\+?\d{9,15}$/.test(phone.value.trim())) return V.note(message, "Số điện thoại không hợp lệ.", "error");
            submit.disabled = true;
            try {
                profile = await V.api("/users/profile", { method: "PUT", body: {
                    full_name: fullName.value.trim(), phone: phone.value.trim() || null, date_of_birth: dob.value || null,
                    gender: gender.value || null, province_id: province.value ? Number(province.value) : null,
                    address: address.value.trim() || null, headline: headline.value.trim() || null,
                    summary: summary.value.trim() || null, visibility: visibility.value } });
                user.full_name = profile.full_name;
                user.phone = profile.phone;
                await attachProvinceName();
                renderHead();
                V.note(message, "Đã lưu hồ sơ.", "success");
            } catch (error) { V.note(message, error.message, "error"); }
            submit.disabled = false;
        });
        box.appendChild(form);
        var avatarFile = h("input", { type: "file", accept: ".jpg,.jpeg,.png,.webp", "aria-label": "Chọn ảnh đại diện" });
        var avatarMessage = h("div", {});
        var uploadAvatar = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Tải ảnh đại diện" });
        var deleteAvatar = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Xóa ảnh đại diện", hidden: !user.avatar_url });
        async function saveAvatar(remove) {
            if (uploadAvatar.disabled) return;
            if (!remove && !avatarFile.files[0]) return V.note(avatarMessage, "Vui lòng chọn ảnh JPG, PNG hoặc WEBP.", "error");
            uploadAvatar.disabled = true; deleteAvatar.disabled = true;
            try {
                var options = { method: remove ? "DELETE" : "POST" };
                if (!remove) { options.formData = new FormData(); options.formData.append("file", avatarFile.files[0]); }
                var result = await V.api("/candidates/me/avatar", options);
                user.avatar_url = result.avatar_url;
                deleteAvatar.hidden = !result.avatar_url;
                avatarFile.value = "";
                renderHead();
                V.note(avatarMessage, remove ? "Đã xóa ảnh đại diện." : "Đã cập nhật ảnh đại diện.", "success");
            } catch (error) { V.note(avatarMessage, error.message, "error"); }
            finally { uploadAvatar.disabled = false; deleteAvatar.disabled = false; }
        }
        uploadAvatar.addEventListener("click", function () { saveAvatar(false); });
        deleteAvatar.addEventListener("click", function () { saveAvatar(true); });
        box.appendChild(h("section", { class: "v-card v-mt-3 v-mb-3" }, h("h2", { class: "v-h3", text: "Ảnh đại diện" }),
            h("p", { class: "v-small v-muted", text: "JPG, PNG hoặc WEBP. Dung lượng tối đa theo cấu hình quản trị." }),
            avatarMessage, avatarFile, h("div", { class: "v-flex v-mt-2" }, uploadAvatar, deleteAvatar)));
        box.appendChild(h("div", { class: "v-card" }, h("h2", { class: "v-h3 v-mb-2", text: "Tài khoản" }),
            h("p", { class: "v-muted v-mb-2", text: "Đổi mật khẩu bằng liên kết gửi qua email, hoặc đăng xuất khỏi thiết bị này." }),
            h("div", { class: "v-flex" },
                h("a", { class: "v-btn v-btn-outline v-btn-sm", href: V.url("pages/account.html") + "?action=forgot-password", text: "Đặt lại mật khẩu" }),
                h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Đăng xuất", onclick: V.logout }))));
    }

    function renderOverview(box) {
        var missing = [];
        if (!profile || !profile.headline) missing.push("chức danh mong muốn");
        if (!profile || !profile.summary) missing.push("giới thiệu bản thân");
        if (!user.phone) missing.push("số điện thoại");
        if (!cvData.total) missing.push("CV");
        if (missing.length) {
            box.appendChild(h("div", { class: "v-banner v-mb-3" },
                h("div", {}, h("h3", { text: "Hoàn thiện hồ sơ để nhà tuyển dụng hiểu bạn hơn" }), h("p", { text: "Còn thiếu: " + missing.join(", ") + "." })),
                h("a", { class: "v-btn v-btn-primary v-btn-sm", href: missing[0] === "CV" ? "#cvs" : "#settings", text: "Cập nhật ngay" })));
        }
        box.appendChild(h("div", { class: "v-card v-mb-3" }, h("h2", { class: "v-card-title", text: "Giới thiệu" }),
            profile && profile.summary ? h("p", { style: "white-space:pre-wrap", text: profile.summary }) : h("p", { class: "v-muted", text: "Bạn chưa viết phần giới thiệu bản thân." })));
        renderApplications(box, 3);
    }

    function renderTab() {
        var tab = currentTab();
        tabsBox.querySelectorAll("a").forEach(function (link) { link.setAttribute("aria-selected", String(link.dataset.tab === tab)); link.classList.toggle("is-active", link.dataset.tab === tab); });
        var panel = h("div", {});
        V.clear(content).appendChild(panel);
        if (tab === "applications") renderApplications(panel);
        else if (tab === "saved") renderSaved(panel);
        else if (tab === "cvs") renderCvs(panel);
        else if (tab === "settings") renderSettings(panel);
        else if (tab === "history") window.ViecoProfileHistory.render(panel);
        else if (tab === "notifications") {
            panel.appendChild(h("h2", { class: "v-h3 v-mb-2", text: "Thông báo" }));
            var box = h("div", {});
            panel.appendChild(box);
            window.ViecoNotifications.mount(box, { onCount: function (unread) { counts.unread = unread; paintCounts(); } });
        } else renderOverview(panel);
    }

    async function attachProvinceName() {
        if (!profile || !profile.province_id) return;
        var data = await V.categories();
        var match = (data.provinces || []).filter(function (item) { return item.id === profile.province_id; })[0];
        profile.province_name = match ? match.name : null;
    }

    async function init() {
        user = await V.requireRole(["CANDIDATE"], app);
        if (!user) return;
        try {
            var account = await V.api("/users/profile");
            profile = account.profile;
            await attachProvinceName();
            cvData = await V.api("/candidates/me/cvs");
        } catch (error) {
            var wrap = h("div", { class: "v-wrap v-section" });
            V.clear(app).appendChild(wrap);
            return V.note(wrap, error.message, "error");
        }
        headBox = h("div", {});
        tabsBox = h("nav", { class: "v-tabs", "aria-label": "Mục hồ sơ" }, TABS.map(function (tab) {
            return h("a", { href: "#" + tab[0], "data-tab": tab[0], "data-label": tab[1], text: tab[1] });
        }));
        content = h("div", {});
        sideCv = h("div", { class: "v-card" });
        var suggestions = h("div", { class: "v-card" }, h("h2", { class: "v-card-title", text: "Việc làm gợi ý cho bạn" }));
        V.clear(app);
        app.appendChild(h("section", { class: "v-page-head", style: "padding-bottom:0" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" }, h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }), h("span", { "aria-current": "page", text: "Hồ sơ của tôi" })),
            headBox,
            h("div", { class: "v-stats" }, stat("applications", "send", "Việc đã ứng tuyển"), stat("saved", "bookmark", "Việc đã lưu"), stat("cvs", "file", "CV của tôi"), stat("unread", "bell", "Thông báo chưa đọc")),
            tabsBox)));
        app.appendChild(h("section", { class: "v-section" }, h("div", { class: "v-wrap v-layout-side v-layout-side-wide" }, content, h("aside", {}, sideCv, suggestions))));
        renderHead();
        renderSideCv();
        renderTab();
        window.addEventListener("hashchange", renderTab);
        document.addEventListener("vieco:saved-changed", function () {
            V.api("/saved-jobs").then(function (data) { counts.saved = data.total; paintCounts(); if (currentTab() === "saved") renderTab(); }).catch(function () {});
        });

        V.api("/applications/my-applications", { query: { page_size: 1 } }).then(function (d) { counts.applications = d.total; paintCounts(); }).catch(function () {});
        V.api("/saved-jobs").then(function (d) { counts.saved = d.total; paintCounts(); }).catch(function () {});
        V.api("/notifications", { query: { page_size: 1 } }).then(function (d) { counts.unread = d.unread_count; paintCounts(); }).catch(function () {});
        V.api("/jobs", { auth: false, query: { page_size: 3, province_id: profile && profile.province_id } }).then(function (data) {
            if (!data.items.length) return suggestions.appendChild(h("p", { class: "v-small v-muted", text: "Chưa có gợi ý phù hợp." }));
            suggestions.appendChild(h("div", {}, data.items.map(function (job) {
                return h("a", { class: "v-kv", href: V.jobUrl(job.id) },
                    h("span", {}, h("strong", { style: "font-weight:500;display:block", text: job.title }), h("span", { class: "v-muted", text: [job.company_name, V.salary(job)].join(" · ") })),
                    V.icon("out"));
            })));
            suggestions.appendChild(h("a", { class: "v-link", href: V.url("pages/jobs.html"), text: "Xem tất cả việc làm ↗" }));
        }).catch(function () {});
    }
    init();
}());
