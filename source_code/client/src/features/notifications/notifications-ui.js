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
        var page = 1;
        var list = h("div", {});
        var pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang thông báo" });
        var summary = h("p", { class: "v-muted", "aria-live": "polite" });
        var readAll = h("button", { type: "button", class: "v-btn v-btn-outline v-btn-xs", text: "Đánh dấu tất cả đã đọc", hidden: true });
        V.clear(container);
        container.appendChild(h("div", { class: "v-results-head" }, summary, readAll));
        container.appendChild(list);
        container.appendChild(pager);

        async function load() {
            V.loading(list, "Đang tải thông báo...");
            try {
                var data = await V.api("/notifications", { query: { page: page, page_size: 10 } });
                summary.textContent = data.total ? data.unread_count + " chưa đọc trong tổng số " + data.total + " thông báo" : "";
                readAll.hidden = !data.unread_count;
                if (options.onCount) options.onCount(data.unread_count, data.total);
                V.clear(list);
                if (!data.items.length) return V.empty(list, "Chưa có thông báo", "Thông báo về đơn ứng tuyển, tin tuyển dụng và công ty sẽ hiển thị tại đây.");
                data.items.forEach(function (item) {
                    var link = target(item.action_url);
                    var row = h("button", { type: "button", class: "v-notif" + (item.is_read ? " is-read" : "") },
                        h("span", { class: "dot", "aria-hidden": "true" }),
                        h("span", {}, h("strong", { text: item.title }), h("p", { text: item.message }),
                            !item.is_read && h("span", { class: "v-sr", text: "Chưa đọc" })),
                        h("time", { text: V.ago(item.created_at) }));
                    row.addEventListener("click", async function () {
                        try {
                            if (!item.is_read) await V.api("/notifications/" + item.id + "/read", { method: "PATCH" });
                        } catch (error) { return V.toast(error.message, true); }
                        V.refreshUnread();
                        if (link) window.location.href = link; else load();
                    });
                    list.appendChild(row);
                });
                V.pagination(pager, data.page, Math.ceil(data.total / data.page_size), function (next) { page = next; load(); });
            } catch (error) {
                V.clear(pager);
                V.note(list, error.message, "error");
            }
        }
        readAll.addEventListener("click", async function () {
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
