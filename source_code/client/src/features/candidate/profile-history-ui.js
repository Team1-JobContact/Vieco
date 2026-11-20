(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var TITLES = { educations: "Học vấn", experiences: "Kinh nghiệm làm việc", skills: "Kỹ năng" };
    var LEVELS = { BEGINNER: "Cơ bản", INTERMEDIATE: "Trung bình", ADVANCED: "Nâng cao" };

    function render(container) {
        var history, categories;
        function field(label, input) { return h("label", { class: "v-field" }, h("span", { text: label }), input); }
        function edit(kind, entry) {
            var data = entry || {}, controls = {}, fields = [];
            function input(key, label, type, max, required) {
                var node = h("input", { class: "v-input", name: key, type: type || "text", value: data[key] || "", maxlength: max, required: required });
                controls[key] = node;
                fields.push(field(label, node));
            }
            if (kind === "educations") {
                input("school_name", "Trường học", "text", 200, true);
                input("major", "Chuyên ngành", "text", 150);
                input("degree", "Bằng cấp", "text", 50);
            } else if (kind === "experiences") {
                input("company_name", "Công ty", "text", 200, true);
                input("position", "Vị trí", "text", 150, true);
            } else {
                var skill = h("select", { name: "skill_id", "aria-label": "Kỹ năng", required: true }, h("option", { value: "", text: "Chọn kỹ năng" }),
                    categories.skills.map(function (row) { return h("option", { value: String(row.id), text: row.name }); }));
                if (entry && !categories.skills.some(function (row) { return row.id === entry.skill_id; })) {
                    skill.appendChild(h("option", { value: String(entry.skill_id), text: entry.name + " (đã ẩn)" }));
                }
                skill.value = data.skill_id ? String(data.skill_id) : "";
                var level = h("select", { name: "level", "aria-label": "Mức độ" }, h("option", { value: "", text: "Chưa chọn" }),
                    Object.keys(LEVELS).map(function (key) { return h("option", { value: key, text: LEVELS[key] }); }));
                level.value = data.level || "";
                controls = { skill_id: skill, level: level };
                fields.push(field("Kỹ năng", skill), field("Mức độ", level));
            }
            if (kind !== "skills") {
                input("start_date", "Ngày bắt đầu", "date", null, kind === "experiences");
                input("end_date", "Ngày kết thúc (để trống nếu đang học / làm)", "date");
                var description = h("textarea", { name: "description", rows: 4, maxlength: 5000, text: data.description || "" });
                controls.description = description;
                fields.push(field("Mô tả", description));
            }
            V.modal(function (close) {
                var message = h("div", {}), busy = false;
                var submit = h("button", { type: "submit", class: "v-btn v-btn-primary v-btn-sm", text: "Lưu" });
                var form = h("form", {}, h("h2", { text: (entry ? "Sửa " : "Thêm ") + TITLES[kind].toLowerCase() }), message, fields,
                    h("div", { class: "v-form-foot" }, h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Hủy", onclick: close }), submit));
                form.addEventListener("submit", async function (event) {
                    event.preventDefault();
                    if (busy || !form.reportValidity()) return;
                    var payload = {};
                    Object.keys(controls).forEach(function (key) { payload[key] = controls[key].value.trim() || null; });
                    if (kind === "skills") payload.skill_id = Number(payload.skill_id);
                    if (payload.start_date && payload.end_date && payload.end_date < payload.start_date) {
                        return V.note(message, "Ngày kết thúc phải từ ngày bắt đầu trở đi", "error");
                    }
                    busy = true; submit.disabled = true;
                    try {
                        await V.api("/candidates/me/history/" + kind + (entry ? "/" + entry.id : ""), { method: entry ? "PUT" : "POST", body: payload });
                        close(); V.toast("Đã lưu hồ sơ"); load();
                    } catch (error) { V.note(message, error.message, "error"); }
                    finally { busy = false; submit.disabled = false; }
                });
                return form;
            }, { label: TITLES[kind] });
        }
        async function remove(kind, entry, button) {
            if (button.disabled) return;
            button.disabled = true;
            try {
                if (!await V.confirm("Xóa mục hồ sơ", "Bạn muốn xóa mục này?", "Xóa", true)) return;
                await V.api("/candidates/me/history/" + kind + "/" + entry.id, { method: "DELETE" });
                V.toast("Đã xóa mục hồ sơ"); load();
            } catch (error) { V.toast(error.message, true); }
            finally { button.disabled = false; }
        }
        function section(kind) {
            var box = h("section", { class: "v-card v-mb-3" }, h("div", { class: "v-results-head" },
                h("h2", { class: "v-h3", text: TITLES[kind] }),
                h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Thêm " + TITLES[kind].toLowerCase(), onclick: function () { edit(kind); } })));
            if (!history[kind].length) box.appendChild(h("p", { class: "v-muted", text: "Chưa cập nhật" }));
            history[kind].forEach(function (entry) {
                var deleteButton = h("button", { type: "button", class: "v-btn v-btn-danger v-btn-xs", text: "Xóa", onclick: function () { remove(kind, entry, deleteButton); } });
                box.appendChild(h("article", { class: "v-card v-mb-2" },
                    h("h3", { class: "v-card-title", text: entry.school_name || entry.company_name || entry.name }),
                    h("p", { text: [entry.major, entry.degree, entry.position, LEVELS[entry.level]].filter(Boolean).join(" · ") }),
                    kind !== "skills" && h("p", { class: "v-small v-muted", text: (entry.start_date ? V.date(entry.start_date) : "Chưa có ngày bắt đầu") + " – " + (entry.end_date ? V.date(entry.end_date) : "Hiện tại") }),
                    entry.description && h("p", { style: "white-space:pre-wrap", text: entry.description }),
                    h("div", { class: "v-row-actions" }, h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", text: "Sửa", onclick: function () { edit(kind, entry); } }), deleteButton)));
            });
            return box;
        }
        async function load() {
            V.loading(container);
            try {
                var results = await Promise.all([V.api("/candidates/me/history"), V.categories()]);
                history = results[0]; categories = results[1];
                V.clear(container);
                Object.keys(TITLES).forEach(function (kind) { container.appendChild(section(kind)); });
            } catch (error) { V.note(container, error.message, "error"); }
        }
        load();
    }
    window.ViecoProfileHistory = { render: render };
}());
