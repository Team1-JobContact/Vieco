/* Danh sách thông báo trong hệ thống (PB-024): chỉ thông báo của chính người dùng, đánh dấu đã đọc. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;

    /** Chỉ điều hướng tới đường dẫn nội bộ đã biết; không dùng URL tùy ý từ dữ liệu. */
    function target(actionUrl) {
        var value = String(actionUrl || "");
        var job = value.match(/^\/employer\/jobs\/(\d+)$/);
        if (job) return V.url("pages/employer-jobs.html") + "?job_id=" + job[1];
        if (value === "/employer/company") return V.url("pages/employer.html");
        if (/^\/pages\/[a-z-]+\.html([?#][\w=&#-]*)?$/.test(value)) return V.url(value.slice(1));
        return null;
    }

    function mount(container, options) {
        options = options || {};
        var page = 1, request = 0;
        var list = h("div", { class: "v-notifications-list" });
        var pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang thông báo" });
        var summary = h("p", { class: "v-notifications-summary", "aria-live": "polite" });
        var readAll = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", hidden: true }, V.icon("check", "v-icon-sm"), "Đánh dấu tất cả đã đọc");
        V.clear(container);
        container.appendChild(h("div", { class: "v-notifications-toolbar" }, summary, readAll));
        container.appendChild(list);
        container.appendChild(pager);

        async function load() {
            var current = ++request;
            V.loading(list, "Đang tải thông báo...");
            V.clear(pager);
            readAll.disabled = true;
            try {
                var data = await V.api("/notifications", { query: { page: page, page_size: 10 } });
                if (current !== request) return;
                V.clear(summary);
                if (data.unread_count) {
                    summary.appendChild(h("strong", { text: data.unread_count + " chưa đọc" }));
                    summary.appendChild(document.createTextNode(" trong " + data.total + " thông báo"));
                } else summary.textContent = data.total ? "Đã đọc tất cả " + data.total + " thông báo" : "0 thông báo";
                readAll.hidden = !data.unread_count;
                if (options.onCount) options.onCount(data.unread_count, data.total);
                V.clear(list);
                if (!data.items.length) {
                    list.appendChild(h("div", { class: "v-notifications-empty" },
                        h("span", { class: "v-notifications-empty-symbol", "aria-hidden": "true" }, V.icon("bell", "v-icon-lg")),
                        h("h3", { text: "Chưa có thông báo" }),
                        h("p", { text: "Thông báo về hồ sơ ứng tuyển, tin tuyển dụng và công ty sẽ xuất hiện tại đây." })));
                    return;
                }
                data.items.forEach(function (item) {
                    var link = target(item.action_url);
                    var name = /^APPLICATION/.test(item.type) ? "file" : /^COMPANY/.test(item.type) ? "globe" : /^JOB/.test(item.type) ? "brief" : "bell";
                    var row = h("button", { type: "button", class: "v-notif" + (item.is_read ? " is-read" : ""), "data-notification-id": item.id },
                        h("span", { class: "v-notif-symbol", "aria-hidden": "true" }, V.icon(name)),
                        h("span", { class: "v-notif-content" }, h("strong", { text: item.title }), h("span", { class: "v-notif-message", text: item.message }),
                            h("span", { class: "v-notif-meta" }, h("span", { class: "v-notif-state", text: item.is_read ? "Đã đọc" : "Chưa đọc" }),
                                item.created_at && h("time", { datetime: item.created_at, title: V.date(item.created_at), text: V.ago(item.created_at) }))),
                        link && h("span", { class: "v-notif-arrow", "aria-hidden": "true" }, V.icon("right", "v-icon-sm")));
                    row.addEventListener("click", async function () {
                        if (row.disabled) return;
                        row.disabled = true;
                        row.setAttribute("aria-busy", "true");
                        try {
                            if (!item.is_read) await V.api("/notifications/" + item.id + "/read", { method: "PATCH" });
                            V.refreshUnread();
                            if (link) window.location.href = link; else await load();
                        } catch (error) { V.toast(error.message, true); }
                        finally { row.disabled = false; row.removeAttribute("aria-busy"); }
                    });
                    list.appendChild(row);
                });
                V.pagination(pager, data.page, Math.ceil(data.total / data.page_size), function (next) { page = next; load(); });
            } catch (error) {
                if (current !== request) return;
                summary.textContent = "";
                readAll.hidden = true;
                V.note(list, error.message, "error");
                list.appendChild(h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Thử lại", onclick: load }));
            } finally {
                if (current === request) readAll.disabled = false;
            }
        }
        readAll.addEventListener("click", async function () {
            if (readAll.disabled) return;
            readAll.disabled = true;
            try {
                await V.api("/notifications/read-all", { method: "PATCH" });
                V.refreshUnread();
                await load();
            } catch (error) { V.toast(error.message, true); }
            readAll.disabled = false;
        });
        load();
    }

    window.ViecoNotifications = { mount: mount, target: target };
}());
