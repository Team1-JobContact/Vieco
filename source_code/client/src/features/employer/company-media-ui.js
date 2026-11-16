/* Hình ảnh công ty: nhà tuyển dụng tự tải logo, ảnh bìa (banner) và ảnh không gian làm việc. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    var company, state, message, body;

    function checkFile(file, maxMb) {
        var ext = file.name.split(".").pop().toLowerCase();
        if (state.limits.allowed_extensions.indexOf(ext) === -1) return "Chỉ chấp nhận ảnh JPG, PNG hoặc WEBP.";
        if (file.size > maxMb * 1024 * 1024) return "Ảnh vượt quá " + maxMb + " MB.";
        return null;
    }

    /** Nút chọn tệp: kiểm tra phía client rồi gửi lên API; kết quả trả về là trạng thái hình ảnh mới. */
    function uploader(label, path, maxMb, doneText) {
        var input = h("input", { type: "file", hidden: true, accept: ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" });
        var button = h("button", { type: "button", class: "v-btn v-btn-primary v-btn-sm" }, label, V.icon("upload"));
        button.addEventListener("click", function () { input.click(); });
        input.addEventListener("change", async function () {
            var file = input.files[0];
            input.value = "";
            if (!file) return;
            var problem = checkFile(file, maxMb);
            if (problem) return V.note(message, problem, "error");
            button.disabled = true;
            V.note(message, "Đang tải ảnh lên...");
            try {
                var data = new FormData();
                data.append("file", file);
                state = await V.api("/employer/company/" + path, { method: "POST", formData: data });
                render();
                V.note(message, doneText, "success");
            } catch (error) {
                V.note(message, error.message, "error");
                button.disabled = false;
            }
        });
        return [button, input];
    }

    async function remove(path, title, text, doneText) {
        if (!(await V.confirm(title, text, "Xóa ảnh", true))) return;
        try {
            state = await V.api("/employer/company/" + path, { method: "DELETE" });
            render();
            V.note(message, doneText, "success");
        } catch (error) { V.note(message, error.message, "error"); }
    }

    function single(title, hint, kind, url, path, maxMb, names) {
        var src = V.media(url);
        var preview = h("div", { class: "v-media-preview is-" + kind },
            src ? h("img", { src: src, alt: names.alt }) : names.empty);
        var actions = state.can_edit ? h("div", { class: "v-flex v-mt-2" },
            uploader(src ? "Thay " + names.short : "Tải " + names.short + " lên", path, maxMb, "Đã cập nhật " + names.short + "."),
            src && h("button", { type: "button", class: "v-btn v-btn-danger v-btn-sm", text: "Xóa " + names.short,
                onclick: function () { remove(path, "Xóa " + names.short + "?", "Trang công ty sẽ không còn hiển thị " + names.short + " này.", "Đã xóa " + names.short + "."); } })) : null;
        return h("section", { class: "v-card v-media-block" },
            h("div", {}, h("h2", { class: "v-h3", text: title }), h("p", { class: "v-muted v-small v-mt-2", text: hint })),
            h("div", {}, preview, actions));
    }

    function gallery() {
        var limits = state.limits, full = state.images.length >= limits.max_images;
        var grid = h("div", { class: "v-media-grid" }, state.images.map(function (image, index) {
            return h("div", { class: "v-media-item" },
                h("img", { src: V.media(image.url), alt: "Ảnh không gian làm việc " + (index + 1), loading: "lazy" }),
                state.can_edit && h("button", { type: "button", "aria-label": "Xóa ảnh không gian làm việc " + (index + 1),
                    onclick: function () { remove("images/" + image.id, "Xóa ảnh này?", "Ảnh sẽ bị gỡ khỏi mục Không gian làm việc trên trang công ty.", "Đã xóa ảnh."); } }, V.icon("trash")));
        }));
        return h("section", { class: "v-card v-media-block" },
            h("div", {}, h("h2", { class: "v-h3", text: "Không gian làm việc" }),
                h("p", { class: "v-muted v-small v-mt-2", text: "Ảnh văn phòng, đội ngũ, hoạt động của công ty. Tối đa " + limits.max_images + " ảnh, mỗi ảnh không quá " + limits.photo_max_mb + " MB." }),
                h("p", { class: "v-small v-mt-2", text: "Đã dùng " + state.images.length + "/" + limits.max_images + " ảnh" })),
            h("div", {},
                state.images.length ? grid : h("div", { class: "v-media-preview is-cover", text: "Chưa có ảnh không gian làm việc" }),
                state.can_edit && h("div", { class: "v-flex v-mt-2" },
                    full ? h("p", { class: "v-small v-muted", text: "Đã đủ số ảnh tối đa. Xóa bớt ảnh để tải ảnh mới." })
                        : uploader("Thêm ảnh", "images", limits.photo_max_mb, "Đã thêm ảnh không gian làm việc."))));
    }

    function render() {
        var limits = state.limits;
        V.clear(body);
        if (!state.can_edit) body.appendChild(h("div", { class: "v-note v-note-warn", text: "Chỉ chủ sở hữu công ty mới thay đổi được hình ảnh. Bạn đang xem ở chế độ chỉ đọc." }));
        body.appendChild(single("Logo công ty", "Hiển thị cạnh tên công ty và trên các tin tuyển dụng. Nên dùng ảnh vuông, nền sáng. JPG, PNG hoặc WEBP, tối đa " + limits.logo_max_mb + " MB.",
            "logo", state.logo_url, "logo", limits.logo_max_mb, { short: "logo", alt: "Logo " + company.name, empty: "Chưa có logo" }));
        body.appendChild(single("Ảnh bìa (banner)", "Hiển thị ở đầu trang công ty và trên thẻ công ty. Nên dùng ảnh ngang, rộng từ 1440 px. JPG, PNG hoặc WEBP, tối đa " + limits.photo_max_mb + " MB.",
            "cover", state.cover_url, "cover", limits.photo_max_mb, { short: "ảnh bìa", alt: "Ảnh bìa " + company.name, empty: "Chưa có ảnh bìa" }));
        body.appendChild(gallery());
    }

    async function init() {
        var user = await V.requireRole(["EMPLOYER"], app);
        if (!user) return;
        message = h("div", {});
        body = h("div", {});
        var wrap = h("div", { class: "v-wrap" }, message, body);
        try {
            company = await V.api("/employer/company");
            state = await V.api("/employer/company/media");
        } catch (error) {
            V.clear(app).appendChild(h("section", { class: "v-section" }, wrap));
            if (error.status === 404) {
                return V.empty(body, "Bạn chưa có hồ sơ công ty", "Tạo hồ sơ công ty trước, sau đó quay lại đây để tải hình ảnh.",
                    h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/employer.html"), text: "Tạo hồ sơ công ty" }));
            }
            return V.note(message, error.message, "error");
        }
        V.clear(app);
        app.appendChild(h("section", { class: "v-page-head" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" },
                h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }),
                h("a", { href: V.url("pages/employer-jobs.html"), text: "Quản lý tuyển dụng" }), h("span", { text: "/" }),
                h("span", { "aria-current": "page", text: "Hình ảnh công ty" })),
            h("div", { class: "v-title-row" },
                h("div", { class: "grow" }, h("p", { class: "v-eyebrow", text: "Nhà tuyển dụng" }),
                    h("h1", { text: "Hình ảnh của " + company.name }),
                    h("p", { class: "v-lead", text: "Logo, ảnh bìa và ảnh không gian làm việc do công ty tự đăng tải sẽ hiển thị trên trang công ty và các tin tuyển dụng." })),
                h("div", { class: "v-title-actions" },
                    company.status === "APPROVED" && h("a", { class: "v-btn v-btn-outline", href: V.companyUrl(company.id) }, "Xem trang công ty", V.icon("out")))))));
        app.appendChild(h("section", { class: "v-section" }, wrap));
        render();
    }
    init();
}());
