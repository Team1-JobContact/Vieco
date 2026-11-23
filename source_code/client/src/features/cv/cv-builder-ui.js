/* Trình tạo CV trực tuyến: chọn mẫu, nhập thông tin, thêm ảnh, xem trước A4, tải PDF,
   lưu vào CV của tôi (để ứng tuyển) và tạo nhanh nội dung bằng AI.
   CV mới đang soạn được lưu nháp trên trình duyệt; CV đã lưu chỉ thay đổi khi bấm "Lưu thay đổi". */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h, CV = window.ViecoCv;
    var app = document.getElementById("app");
    var params = new URLSearchParams(window.location.search);
    var DRAFT_KEY = "vieco.cvBuilder.draft";
    var AI_MAX = 8000;

    var PERSONAL_FORM = [
        ["full_name", "Họ và tên *", "Nguyễn Minh Anh", 150, "text"],
        ["title", "Vị trí ứng tuyển", "Marketing Specialist", 150, "text"],
        ["birthday", "Ngày sinh", "15/08/2001", 30, "text"],
        ["phone", "Số điện thoại", "0901 234 567", 30, "tel"],
        ["email", "Email", "minhanh@example.com", 254, "email"],
        ["address", "Địa chỉ", "Quận 1, TP. Hồ Chí Minh", 255, "text"],
        ["link", "Website / LinkedIn", "linkedin.com/in/minhanh", 255, "text"]
    ];
    var SECTION_FORM = {
        experience: { title: "Kinh nghiệm làm việc", item: "Kinh nghiệm", add: "Thêm kinh nghiệm", labels: ["Vị trí / chức danh", "Công ty"],
            examples: ["Marketing Executive", "Công ty Cổ phần ABC"], desc: "Công việc và thành tích, mỗi dòng một ý" },
        education: { title: "Học vấn", item: "Học vấn", add: "Thêm học vấn", labels: ["Trường", "Chuyên ngành / bằng cấp"],
            examples: ["Đại học Kinh tế TP. Hồ Chí Minh", "Cử nhân Marketing"], desc: "GPA, đề tài, thành tích, mỗi dòng một ý" },
        projects: { title: "Dự án", item: "Dự án", add: "Thêm dự án", labels: ["Tên dự án", "Vai trò / công nghệ"],
            examples: ["Website bán hàng", "Trưởng nhóm · React, Node.js"], desc: "Mục tiêu, việc bạn làm, kết quả, mỗi dòng một ý" },
        activities: { title: "Hoạt động", item: "Hoạt động", add: "Thêm hoạt động", labels: ["Hoạt động / tổ chức", "Vai trò"],
            examples: ["CLB Tình nguyện Xanh", "Trưởng ban truyền thông"], desc: "Đóng góp và kết quả, mỗi dòng một ý" }
    };
    var LIST_FORM = {
        skills: { title: "Kỹ năng", hint: "Mỗi dòng một kỹ năng", placeholder: "Phân tích dữ liệu\nSQL\nGiao tiếp" },
        languages: { title: "Ngoại ngữ", hint: "Mỗi dòng một ngoại ngữ kèm trình độ", placeholder: "Tiếng Anh – IELTS 7.0" },
        certificates: { title: "Chứng chỉ & giải thưởng", hint: "Mỗi dòng một mục", placeholder: "Google Analytics Certification (2023)" },
        interests: { title: "Sở thích", hint: "Mỗi dòng một sở thích", placeholder: "Đọc sách\nChạy bộ" }
    };
    var ENTRY_MAX = { title: 200, subtitle: 200, start: 30, end: 30, description: 3000 };
    var AI_EXAMPLE = "Ví dụ: Tôi là Nguyễn Minh Anh, sinh 15/08/2001, sống ở Quận 1, TP.HCM, sđt 0901234567, email minhanh@example.com. " +
        "Tốt nghiệp ĐH Kinh tế TP.HCM ngành Marketing năm 2023, GPA 3.4. Từ 07/2023 đến nay làm Marketing Executive ở công ty ABC: " +
        "lên kế hoạch nội dung fanpage, chạy quảng cáo Facebook, tăng 40% lượt tương tác. Thành thạo Canva, Google Analytics, tiếng Anh IELTS 7.0...";

    var state = { data: CV.empty(), cvId: null, dirty: false, busy: false };
    var ui = {};
    var renderTimer = null, draftTimer = null;

    // ---------- Bản nháp trên trình duyệt (chỉ cho CV mới chưa lưu) ----------
    function readDraft() {
        try {
            var draft = JSON.parse(window.localStorage.getItem(DRAFT_KEY) || "null");
            return draft && draft.data ? draft : null;
        } catch (_) { return null; }
    }
    function saveDraft() {
        clearTimeout(draftTimer);
        if (state.cvId) return;
        try { window.localStorage.setItem(DRAFT_KEY, JSON.stringify({ data: state.data, savedAt: Date.now() })); } catch (_) { /* hết dung lượng hoặc bị chặn */ }
    }
    function clearDraft() { try { window.localStorage.removeItem(DRAFT_KEY); } catch (_) { /* bỏ qua */ } }

    function changed() {
        state.dirty = true;
        clearTimeout(renderTimer);
        renderTimer = setTimeout(renderPreview, 120);
        clearTimeout(draftTimer);
        draftTimer = setTimeout(saveDraft, 500);
    }

    // ---------- Ô nhập liệu ----------
    function field(label, control, hint) {
        return h("label", { class: "v-field" }, h("span", { text: label }), control, hint || null);
    }
    function textInput(value, max, placeholder, onInput, type) {
        return h("input", { type: type || "text", value: value, maxlength: max, placeholder: placeholder,
            oninput: function (event) { onInput(event.target.value); changed(); } });
    }
    function textArea(value, max, placeholder, rows, onInput) {
        return h("textarea", { value: value, maxlength: max, placeholder: placeholder, rows: rows || 4,
            oninput: function (event) { onInput(event.target.value); changed(); } });
    }
    function card(title, note, body) {
        return h("section", { class: "v-card cvb-card" }, h("div", { class: "cvb-card-head" }, h("h2", { text: title }), note ? h("small", { text: note }) : null), body);
    }
    function iconButton(name, label, disabled, onClick, danger) {
        return h("button", { type: "button", class: "cvb-icon-btn" + (danger ? " is-danger" : ""), "aria-label": label, title: label, disabled: disabled, onclick: onClick }, V.icon(name, "v-icon-sm"));
    }

    /** Ảnh chân dung: cắt khung 3x4, thu nhỏ và nén JPEG ngay trên trình duyệt (không tải ảnh gốc lên máy chủ). */
    function readPhoto(file) {
        return new Promise(function (resolve, reject) {
            if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return reject(new Error("Chỉ nhận ảnh JPG, PNG hoặc WEBP."));
            if (file.size > 10 * 1024 * 1024) return reject(new Error("Ảnh tối đa 10 MB."));
            var src = URL.createObjectURL(file), img = new Image();
            img.onload = function () {
                URL.revokeObjectURL(src);
                var w = img.naturalWidth, hgt = img.naturalHeight, cw = w, ch = w * 4 / 3;
                if (ch > hgt) { ch = hgt; cw = hgt * 3 / 4; }
                var canvas = document.createElement("canvas");
                canvas.width = 360; canvas.height = 480;
                var ctx = canvas.getContext("2d");
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(0, 0, 360, 480);
                ctx.drawImage(img, (w - cw) / 2, (hgt - ch) * 0.3, cw, ch, 0, 0, 360, 480);
                var url = canvas.toDataURL("image/jpeg", 0.86);
                if (url.length > 380000) url = canvas.toDataURL("image/jpeg", 0.7);
                resolve(url);
            };
            img.onerror = function () { URL.revokeObjectURL(src); reject(new Error("Không đọc được ảnh này, hãy chọn ảnh khác.")); };
            img.src = src;
        });
    }

    function personalCard() {
        var box = h("div", { class: "cvb-photo-box" });
        var input = h("input", { type: "file", accept: "image/jpeg,image/png,image/webp", hidden: true });
        var chooseLabel = h("span", {});
        var remove = h("button", { type: "button", class: "v-btn v-btn-danger v-btn-xs", onclick: function () {
            state.data.photo = null; paintPhoto(); changed();
        } }, V.icon("trash", "v-icon-sm"), "Xóa ảnh");
        var message = h("div", {});
        function paintPhoto() {
            V.clear(box).appendChild(state.data.photo ? h("img", { src: state.data.photo, alt: "Ảnh trong CV" }) : h("span", { text: "Ảnh 3x4" }));
            remove.hidden = !state.data.photo;
            chooseLabel.textContent = state.data.photo ? "Đổi ảnh" : "Chọn ảnh";
        }
        input.addEventListener("change", async function () {
            var file = input.files[0];
            input.value = "";
            if (!file) return;
            try {
                state.data.photo = await readPhoto(file);
                V.note(message, "");
                paintPhoto();
                changed();
            } catch (error) { V.note(message, error.message, "error"); }
        });
        paintPhoto();
        var fields = {};
        PERSONAL_FORM.forEach(function (f) {
            fields[f[0]] = field(f[1], textInput(state.data.personal[f[0]], f[3], f[2], function (value) { state.data.personal[f[0]] = value; }, f[4]));
        });
        ui.nameInput = fields.full_name.querySelector("input");
        return card("Thông tin cá nhân", "* bắt buộc", [
            h("div", { class: "cvb-photo" }, box, h("div", {},
                h("strong", { class: "cvb-photo-title", text: "Ảnh chân dung" }),
                h("p", { class: "v-small v-muted", text: "JPG, PNG hoặc WEBP. Ảnh được cắt theo khung 3x4 và chỉ dùng trong CV này." }),
                h("div", { class: "cvb-photo-actions" },
                    h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", onclick: function () { input.click(); } }, V.icon("upload", "v-icon-sm"), chooseLabel),
                    remove), input)),
            message, fields.full_name, fields.title,
            h("div", { class: "v-field-row" }, fields.birthday, fields.phone),
            h("div", { class: "v-field-row" }, fields.email, fields.address),
            fields.link
        ]);
    }

    function summaryCard() {
        return card("Giới thiệu bản thân", "Mục tiêu nghề nghiệp, điểm mạnh", field("Đoạn giới thiệu ngắn",
            textArea(state.data.summary, 3000, "Chuyên viên Marketing với 2 năm kinh nghiệm xây dựng nội dung số...", 4, function (value) { state.data.summary = value; })));
    }

    function sectionCard(key) {
        var meta = SECTION_FORM[key], list = h("div", {});
        var add = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm cvb-add" }, V.icon("plus"), meta.add);
        function paint() {
            var items = state.data[key];
            V.clear(list);
            items.forEach(function (entry, index) {
                function move(delta) {
                    var other = items[index + delta];
                    items[index + delta] = entry;
                    items[index] = other;
                    paint();
                    changed();
                }
                async function removeEntry() {
                    var filled = ["title", "subtitle", "start", "end", "description"].some(function (k) { return entry[k].trim(); });
                    if (filled && !(await V.confirm("Xóa mục này?", "“" + (entry.title.trim() || meta.item + " " + (index + 1)) + "” sẽ bị xóa khỏi CV.", "Xóa", true))) return;
                    items.splice(items.indexOf(entry), 1);
                    paint();
                    changed();
                }
                list.appendChild(h("div", { class: "cvb-entry" },
                    h("div", { class: "cvb-entry-head" }, h("span", { text: meta.item + " " + (index + 1) }), h("div", { class: "cvb-entry-tools" },
                        iconButton("up", "Đưa lên trên", index === 0, function () { move(-1); }),
                        iconButton("down", "Đưa xuống dưới", index === items.length - 1, function () { move(1); }),
                        iconButton("trash", "Xóa mục này", false, removeEntry, true))),
                    h("div", { class: "v-field-row" },
                        field(meta.labels[0], textInput(entry.title, ENTRY_MAX.title, meta.examples[0], function (v) { entry.title = v; })),
                        field(meta.labels[1], textInput(entry.subtitle, ENTRY_MAX.subtitle, meta.examples[1], function (v) { entry.subtitle = v; }))),
                    h("div", { class: "v-field-row" },
                        field("Từ", textInput(entry.start, ENTRY_MAX.start, "MM/YYYY", function (v) { entry.start = v; })),
                        field("Đến", textInput(entry.end, ENTRY_MAX.end, "MM/YYYY hoặc Hiện tại", function (v) { entry.end = v; }))),
                    field("Mô tả", textArea(entry.description, ENTRY_MAX.description, meta.desc, 4, function (v) { entry.description = v; }))));
            });
            add.disabled = items.length >= CV.LIMITS[key];
        }
        add.addEventListener("click", function () {
            state.data[key].push({ title: "", subtitle: "", start: "", end: "", description: "" });
            paint();
            changed();
            var inputs = list.lastChild && list.lastChild.querySelectorAll("input");
            if (inputs && inputs[0]) inputs[0].focus();
        });
        paint();
        return card(meta.title, "Tối đa " + CV.LIMITS[key] + " mục", [list, add]);
    }

    function listCard(key) {
        var meta = LIST_FORM[key], limit = CV.LIMITS[key];
        var hint = h("small", { class: "cvb-hint" });
        function paintHint() {
            var count = state.data[key].length;
            hint.textContent = count > limit ? "Đã nhập " + count + " mục, tối đa " + limit + " mục." : count + "/" + limit + " mục";
            hint.classList.toggle("is-over", count > limit);
        }
        var area = textArea(state.data[key].join("\n"), 6000, meta.placeholder, 4, function (value) {
            state.data[key] = value.split(/\r?\n/).map(function (s) { return s.trim(); }).filter(Boolean);
            paintHint();
        });
        paintHint();
        return card(meta.title, null, field(meta.hint, area, hint));
    }

    function buildForm() {
        V.clear(ui.form);
        [personalCard(), summaryCard(), sectionCard("experience"), sectionCard("education"), listCard("skills"), listCard("languages"),
            sectionCard("projects"), sectionCard("activities"), listCard("certificates"), listCard("interests")].forEach(function (node) { ui.form.appendChild(node); });
        paintTemplates();
    }

    // ---------- Chọn mẫu và các nút thao tác ----------
    function paintTemplates() {
        ui.templates.querySelectorAll(".cvb-template").forEach(function (button) {
            button.setAttribute("aria-pressed", String(button.dataset.template === state.data.template));
        });
    }
    function toolbar() {
        ui.templates = h("div", { class: "cvb-templates", role: "group", "aria-label": "Chọn mẫu CV" }, h("span", { class: "label", text: "Mẫu CV" }),
            Object.keys(CV.TEMPLATES).map(function (key) {
                var template = CV.TEMPLATES[key];
                return h("button", { type: "button", class: "cvb-template", "data-template": key, title: template.note, onclick: function () {
                    if (state.data.template === key) return;
                    state.data.template = key;
                    paintTemplates();
                    changed();
                } }, h("span", { class: "swatch", style: "--swatch:" + template.color, "aria-hidden": "true" }), template.name);
            }));
        ui.aiButton = h("button", { type: "button", class: "v-btn v-btn-gold v-btn-sm", onclick: openAi }, V.icon("spark"), "Tạo bằng AI");
        ui.downloadButton = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", onclick: download }, V.icon("download"), "Tải PDF");
        ui.saveLabel = h("span", {});
        ui.saveButton = h("button", { type: "button", class: "v-btn v-btn-primary v-btn-sm", onclick: save }, V.icon("check"), ui.saveLabel);
        return h("div", { class: "cvb-toolbar" }, ui.templates, h("div", { class: "cvb-actions" }, ui.aiButton, ui.downloadButton, ui.saveButton,
            h("a", { class: "v-link cvb-jump", href: "#cvb-preview", text: "Xem bản xem trước ↓" })));
    }
    function paintMode() {
        var editing = Boolean(state.cvId);
        ui.title.textContent = editing ? "Chỉnh sửa CV" : "Tạo CV trực tuyến";
        ui.crumb.textContent = editing ? "Chỉnh sửa CV" : "Tạo CV";
        ui.saveLabel.textContent = editing ? "Lưu thay đổi" : "Lưu vào CV của tôi";
        document.title = (editing ? "Chỉnh sửa CV" : "Tạo CV") + " | Vieco";
    }

    // ---------- Xem trước ----------
    function previewPane() {
        ui.pageInfo = h("span", {});
        ui.scale = h("div", { class: "cvb-scale" });
        ui.frame = h("div", { class: "cvb-frame" }, ui.scale);
        ui.stage = h("div", { class: "cvb-stage" }, ui.frame);
        return h("aside", { class: "cvb-preview", id: "cvb-preview", "aria-label": "Xem trước CV" },
            h("div", { class: "cvb-preview-head" }, h("strong", { text: "Xem trước" }), ui.pageInfo), ui.stage);
    }
    function fitPreview() {
        var sheet = ui.scale.firstChild;
        if (!sheet) return;
        var style = window.getComputedStyle(ui.stage);
        var width = ui.stage.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
        var scale = Math.min(1, Math.max(0.2, width / CV.PAGE_W));
        ui.scale.style.transform = "scale(" + scale + ")";
        ui.frame.style.width = Math.floor(CV.PAGE_W * scale) + "px";
        ui.frame.style.height = Math.ceil(sheet.offsetHeight * scale) + "px";
    }
    function renderPreview() {
        clearTimeout(renderTimer);
        var sheet = CV.render(state.data, { placeholder: true });
        V.clear(ui.scale).appendChild(sheet);
        var pages = CV.paginate(sheet);
        CV.markPages(sheet, pages);
        ui.pageInfo.textContent = pages + " trang A4 · mẫu " + CV.TEMPLATES[state.data.template].name;
        fitPreview();
    }

    // ---------- Tải PDF và lưu ----------
    function fileName() {
        var p = state.data.personal;
        var base = ["CV", p.full_name.trim(), p.title.trim()].filter(Boolean).join(" - ").replace(/[\\/:*?"<>|]+/g, " ").replace(/\s+/g, " ").trim();
        return base.slice(0, 120) + ".pdf";
    }
    function requireName() {
        if (state.data.personal.full_name.trim()) return true;
        V.note(ui.status, "Hãy nhập họ và tên trước khi tải hoặc lưu CV.", "error");
        ui.nameInput.focus();
        return false;
    }
    function setBusy(busy, message) {
        state.busy = busy;
        [ui.saveButton, ui.downloadButton, ui.aiButton].forEach(function (button) { button.disabled = busy; });
        if (message) V.note(ui.status, message);
    }
    function noteWithLink(kind, message, href, label) {
        V.clear(ui.status).appendChild(h("div", { class: "v-note v-note-" + kind, role: kind === "error" ? "alert" : "status" },
            h("span", { class: "v-note-message" }, message + " ", h("a", { class: "v-link", href: href, text: label }))));
    }
    async function download() {
        if (state.busy || !requireName()) return;
        setBusy(true, "Đang tạo tệp PDF...");
        try {
            var blob = await CV.exportPdf(state.data, fileName().replace(/\.pdf$/, ""));
            var link = h("a", { href: URL.createObjectURL(blob), download: fileName() });
            document.body.appendChild(link);
            link.click();
            setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 1000);
            V.note(ui.status, "Đã tạo tệp “" + fileName() + "”. Kiểm tra thư mục tải xuống của trình duyệt.", "success");
        } catch (error) {
            V.note(ui.status, error.message || "Không tạo được tệp PDF, vui lòng thử lại.", "error");
        }
        setBusy(false);
    }
    async function save() {
        if (state.busy) return;
        var user = await V.currentUser().catch(function () { return null; });
        if (!user) {
            saveDraft();
            return V.goLogin();
        }
        if (user.role !== "CANDIDATE") {
            return V.note(ui.status, "Chỉ tài khoản ứng viên mới lưu được CV vào mục CV của tôi. Bạn vẫn có thể tải PDF về máy.", "warn");
        }
        if (!requireName()) return;
        var editing = state.cvId;
        setBusy(true, editing ? "Đang lưu thay đổi..." : "Đang tạo tệp PDF và lưu vào CV của tôi...");
        try {
            var blob = await CV.exportPdf(state.data, fileName().replace(/\.pdf$/, ""));
            var form = new FormData();
            form.append("file", blob, fileName());
            form.append("data", JSON.stringify(state.data));
            var cv = await V.api("/candidates/me/cvs/" + (editing ? encodeURIComponent(editing) + "/builder" : "builder"),
                { method: editing ? "PUT" : "POST", formData: form, timeout: 60000 });
            state.cvId = cv.id;
            state.dirty = false;
            clearDraft();
            window.history.replaceState(null, "", window.location.pathname + "?cv=" + encodeURIComponent(cv.id));
            paintMode();
            noteWithLink("success", "Đã lưu “" + cv.file_name + "” vào CV của tôi. Bạn có thể dùng CV này khi ứng tuyển.", V.url("pages/profile.html#cvs"), "Xem CV của tôi ↗");
        } catch (error) {
            if (editing && error.status === 404) {
                state.cvId = null;
                paintMode();
                saveDraft();
                V.note(ui.status, "CV này không còn trong mục CV của tôi. Bấm “Lưu vào CV của tôi” để lưu thành CV mới.", "warn");
            } else if (error.status === 409) {
                noteWithLink("error", error.message + ".", V.url("pages/profile.html#cvs"), "Mở CV của tôi ↗");
            } else {
                V.note(ui.status, error.message || "Không lưu được CV, vui lòng thử lại.", "error");
            }
        }
        setBusy(false);
    }

    // ---------- Tạo CV bằng AI ----------
    /** Mục AI tạo được thì thay nội dung hiện tại; ảnh, mẫu và những mục AI để trống được giữ nguyên. */
    function applyAi(content) {
        var next = CV.normalize(content), current = state.data;
        CV.PERSONAL.forEach(function (key) { if (!next.personal[key].trim()) next.personal[key] = current.personal[key]; });
        if (!next.summary.trim()) next.summary = current.summary;
        CV.SECTIONS.concat(CV.LISTS).forEach(function (key) { if (!next[key].length) next[key] = current[key]; });
        next.photo = current.photo;
        next.template = current.template;
        state.data = next;
        buildForm();
        renderPreview();
        changed();
    }
    function openAi() {
        if (state.busy) return;
        var open = true;
        V.modal(function (close) {
            var target = h("input", { type: "text", maxlength: 150, value: state.data.personal.title, placeholder: "Ví dụ: Nhân viên Marketing" });
            var info = h("textarea", { maxlength: AI_MAX, rows: 10, placeholder: AI_EXAMPLE });
            var count = h("p", { class: "cvb-ai-count", text: "0/" + AI_MAX });
            var message = h("div", { "aria-live": "polite" });
            var submit = h("button", { type: "submit", class: "v-btn v-btn-gold v-btn-sm" }, V.icon("spark"), "Tạo CV");
            info.addEventListener("input", function () { count.textContent = info.value.length + "/" + AI_MAX; });
            var form = h("form", { class: "cvb-ai", novalidate: true },
                h("p", { class: "v-eyebrow", text: "Trợ lý AI" }),
                h("h2", { text: "Tạo CV bằng AI" }),
                h("p", { class: "v-modal-sub", text: "Nhập tất cả thông tin của bạn: học vấn, kinh nghiệm, dự án, kỹ năng, chứng chỉ... AI sẽ sắp xếp và viết thành CV hoàn chỉnh theo mẫu đang chọn. Bạn chỉnh sửa lại được trước khi lưu." }),
                field("Vị trí muốn ứng tuyển (không bắt buộc)", target),
                field("Thông tin của bạn", info), count,
                CV.hasContent(state.data) ? h("div", { class: "v-note v-note-warn" }, h("span", { class: "v-note-message", text: "Các mục AI tạo được sẽ thay nội dung đang có. Ảnh, mẫu CV và các mục AI để trống được giữ nguyên." })) : null,
                h("p", { class: "cvb-ai-privacy", text: "Thông tin bạn nhập được gửi tới dịch vụ AI (Claude của Anthropic) để tạo nội dung. Không nhập mật khẩu, số CCCD hay số tài khoản ngân hàng." }),
                message,
                h("div", { class: "cvb-ai-actions" }, h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Hủy", onclick: close }), submit));
            form.addEventListener("submit", async function (event) {
                event.preventDefault();
                var text = info.value.trim();
                if (text.length < 30) {
                    V.note(message, "Hãy nhập ít nhất 30 ký tự thông tin về bản thân để AI tạo CV.", "error");
                    info.focus();
                    return;
                }
                var user = await V.currentUser().catch(function () { return null; });
                if (!user) {
                    saveDraft();
                    V.clear(message).appendChild(h("div", { class: "v-note v-note-warn" }, h("span", { class: "v-note-message" },
                        "Đăng nhập tài khoản ứng viên để dùng AI. Bản nháp CV của bạn vẫn được giữ. ",
                        h("button", { type: "button", class: "v-link", text: "Đăng nhập ↗", onclick: V.goLogin }))));
                    return;
                }
                if (user.role !== "CANDIDATE") return V.note(message, "Tính năng tạo CV bằng AI dành cho tài khoản ứng viên.", "warn");
                submit.disabled = info.disabled = target.disabled = true;
                V.note(message, "AI đang viết CV, thường mất 20–60 giây. Vui lòng giữ cửa sổ này mở.");
                try {
                    var result = await V.api("/candidates/me/cvs/builder/ai", { method: "POST", body: { text: text, target: target.value.trim() || null }, timeout: 200000 });
                    if (!open) return;   // người dùng đã đóng hộp thoại: không tự thay nội dung
                    applyAi(result.data);
                    close();
                    V.toast("AI đã tạo nội dung CV. Hãy đọc lại và chỉnh sửa cho chính xác trước khi lưu.");
                } catch (error) {
                    if (!open) return;
                    V.note(message, error.message, "error");
                    submit.disabled = info.disabled = target.disabled = false;
                }
            });
            return form;
        }, { label: "Tạo CV bằng AI", className: "cvb-ai-modal", onClose: function () { open = false; } });
    }

    // ---------- Tối ưu CV theo tin tuyển dụng (mở từ trang chi tiết việc làm) ----------
    /** AI viết lại CV đã chọn cho khớp với tin. Kết quả là CV mới chưa lưu; CV gốc giữ nguyên. */
    async function runTailor(jobId, cvId) {
        window.history.replaceState(null, "", window.location.pathname); // tải lại trang không gọi AI thêm lần nữa
        var draft = readDraft();
        var hasDraft = Boolean(draft && CV.hasContent(CV.normalize(draft.data)));
        function restoreDraft() {
            if (!hasDraft) return;
            state.data = CV.normalize(draft.data);
            buildForm();
            renderPreview();
        }
        if (hasDraft && !(await V.confirm("Thay bản nháp đang làm dở?", "CV do AI tối ưu sẽ thay bản nháp CV chưa lưu trên trình duyệt này. CV đã lưu trong mục CV của tôi không bị ảnh hưởng.", "Tiếp tục tối ưu"))) {
            restoreDraft();
            showRestoredNote();
            return;
        }
        setBusy(true);
        ui.form.classList.add("cvb-busy");
        ui.form.setAttribute("aria-busy", "true");
        ui.form.inert = true;
        V.clear(ui.status).appendChild(h("div", { class: "v-note cvb-working", role: "status" },
            h("span", { class: "v-note-message" }, V.icon("spark", "v-icon-sm"), " AI đang đọc tin tuyển dụng và tối ưu CV của bạn, thường mất 20–60 giây. Vui lòng giữ trang này mở.")));
        try {
            var result = await V.api("/candidates/me/cvs/builder/tailor", { method: "POST", body: { job_id: Number(jobId), cv_id: Number(cvId) }, timeout: 200000 });
            state.data = CV.normalize(Object.assign({}, result.data, { template: result.template, photo: result.photo }));
            state.cvId = null;
            state.dirty = true;
            buildForm();
            renderPreview();
            saveDraft();
            paintMode();
            V.clear(ui.status).appendChild(h("div", { class: "v-note v-note-success cvb-tailor", role: "status" },
                h("div", { class: "v-note-message" },
                    h("strong", { text: "AI đã tối ưu CV cho vị trí “" + result.job_title + "”" + (result.company_name ? " tại " + result.company_name : "") + "." }),
                    result.changes.length ? h("ul", {}, result.changes.map(function (change) { return h("li", { text: change }); })) : null,
                    h("p", {}, "Đây là bản CV mới, CV gốc vẫn giữ nguyên. Hãy đọc lại, chỉnh cho đúng với thực tế rồi bấm “Lưu vào CV của tôi” để dùng khi ứng tuyển. ",
                        h("a", { class: "v-link", href: V.jobUrl(result.job_id), text: "Quay lại tin tuyển dụng ↗" })))));
        } catch (error) {
            restoreDraft();
            noteWithLink("error", (error.message || "Không tối ưu được CV, vui lòng thử lại.") + ".", V.jobUrl(jobId), "Quay lại tin tuyển dụng ↗");
        }
        ui.form.classList.remove("cvb-busy");
        ui.form.removeAttribute("aria-busy");
        ui.form.inert = false;
        setBusy(false);
    }

    // ---------- Khởi tạo ----------
    async function prefill() {
        try {
            var user = await V.currentUser();
            if (!user || user.role !== "CANDIDATE") return;
            var account = await V.api("/users/profile"), profile = account.profile || {}, p = state.data.personal;
            p.full_name = account.full_name || "";
            p.email = account.email || "";
            p.phone = account.phone || "";
            p.title = profile.headline || "";
            p.address = profile.address || "";
        } catch (_) { /* không lấy được thông tin tài khoản thì để trống */ }
    }
    function showRestoredNote() {
        var reset = h("button", { type: "button", class: "v-link", text: "Bắt đầu CV mới", onclick: async function () {
            if (!(await V.confirm("Bắt đầu CV mới?", "Bản nháp đang làm dở sẽ bị xóa khỏi trình duyệt này.", "Bắt đầu lại", true))) return;
            var template = state.data.template;
            clearDraft();
            state.data = CV.empty();
            state.data.template = template;
            await prefill();
            state.dirty = false;
            buildForm();
            renderPreview();
            V.note(ui.status, "");
        } });
        V.clear(ui.status).appendChild(h("div", { class: "v-note", role: "status" },
            h("span", { class: "v-note-message" }, "Đã mở lại bản nháp CV bạn đang làm dở trên trình duyệt này. ", reset)));
    }
    function build() {
        ui.title = h("h1", { class: "v-h1" });
        ui.crumb = h("span", { "aria-current": "page" });
        ui.form = h("div", { class: "cvb-form" });
        ui.status = h("div", { class: "cvb-status" });
        V.clear(app);
        app.appendChild(h("section", { class: "v-page-head" }, h("div", { class: "v-wrap" },
            h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" },
                h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }),
                h("a", { href: V.url("pages/cv-library.html"), text: "Thư viện CV" }), h("span", { text: "/" }), ui.crumb),
            h("p", { class: "v-eyebrow", text: "Trình tạo CV" }), ui.title,
            h("p", { class: "v-lead", text: "Chọn mẫu, nhập thông tin và xem trước CV ngay khi gõ. Tải PDF về máy hoặc lưu vào CV của tôi để ứng tuyển chỉ với một lần bấm." }))));
        app.appendChild(h("section", { class: "v-section cvb-section" }, h("div", { class: "v-wrap" },
            toolbar(), ui.status, h("div", { class: "cvb-layout" }, ui.form, previewPane()))));
        buildForm();
        paintMode();
        renderPreview();
        if (window.ResizeObserver) new ResizeObserver(fitPreview).observe(ui.stage);
        else window.addEventListener("resize", fitPreview);
    }
    async function init() {
        var id = params.get("cv"), restored = false;
        var tailorJob = params.get("tailor_job"), fromCv = params.get("from_cv");
        var tailoring = !id && /^[1-9]\d*$/.test(tailorJob || "") && /^[1-9]\d*$/.test(fromCv || "");
        if (tailoring) {
            if (!(await V.requireRole(["CANDIDATE"], app))) return;
        } else if (id) {
            if (!(await V.requireRole(["CANDIDATE"], app))) return;
            try {
                var saved = await V.api("/candidates/me/cvs/" + encodeURIComponent(id) + "/builder");
                state.data = CV.normalize(saved.data);
                state.cvId = saved.cv.id;
            } catch (error) {
                V.clear(app).appendChild(h("section", { class: "v-section" }, h("div", { class: "v-wrap" }, h("div", { class: "v-empty" },
                    h("h3", { text: "Không mở được CV này" }), h("p", { text: error.message }),
                    h("a", { class: "v-btn v-btn-primary v-btn-sm", href: V.url("pages/cv-builder.html"), text: "Tạo CV mới" })))));
                return;
            }
        } else {
            var draft = readDraft();
            if (draft) {
                state.data = CV.normalize(draft.data);
                restored = CV.hasContent(state.data);
            } else {
                await prefill();
            }
        }
        if (CV.TEMPLATES[params.get("template")]) state.data.template = params.get("template");
        build();
        if (restored) showRestoredNote();
        if (document.fonts && document.fonts.ready) document.fonts.ready.then(renderPreview);
        if (tailoring) runTailor(tailorJob, fromCv);
        else if (params.get("ai") === "1") openAi();
        window.addEventListener("beforeunload", function (event) {
            if (state.cvId && state.dirty) { event.preventDefault(); event.returnValue = ""; }
        });
        window.addEventListener("pagehide", function () { if (state.dirty) saveDraft(); });
    }
    init();
}());
