/* Danh sách công ty đã được duyệt: tìm theo tên, lọc địa điểm và ngành, phân trang. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var app = document.getElementById("app");
    var state = { q: "", province_id: "", industry_id: "", page: 1 };
    var request = 0, timer = null;

    var input = h("input", { type: "search", placeholder: "Tìm theo tên công ty", "aria-label": "Tìm theo tên công ty" });
    var province = h("select", { "aria-label": "Địa điểm" }, h("option", { value: "", text: "Tất cả địa điểm" }));
    var tabs = h("div", { class: "v-filter-tabs", role: "group", "aria-label": "Lọc theo ngành" });
    var total = h("span", { class: "v-muted v-small", "aria-live": "polite" });
    var grid = h("div", { class: "v-grid-3" });
    var pager = h("nav", { class: "v-pagination", "aria-label": "Phân trang" });

    V.clear(app);
    app.appendChild(h("section", { class: "v-page-head" }, h("div", { class: "v-wrap" },
        h("nav", { class: "v-crumbs", "aria-label": "Đường dẫn" }, h("a", { href: V.url("index.html"), text: "Trang chủ" }), h("span", { text: "/" }), h("span", { "aria-current": "page", text: "Công ty" })),
        h("p", { class: "v-eyebrow", text: "Nơi bạn có thể thuộc về" }),
        h("h1", { class: "v-h1", text: "Khám phá các công ty hàng đầu" }),
        h("p", { class: "v-lead", text: "Tìm hiểu môi trường làm việc và chọn điểm đến phù hợp cho hành trình của bạn." }),
        h("div", { class: "v-searchbar v-searchbar-white", style: "max-width:760px;margin-top:28px;min-height:0;grid-template-columns:1fr 1px minmax(180px,240px)" },
            h("label", {}, V.icon("search"), input), h("span", { class: "divider" }), h("label", {}, V.icon("pin"), province)))));
    app.appendChild(h("section", { class: "v-section" }, h("div", { class: "v-wrap" },
        h("div", { class: "v-results-head" }, tabs, total), grid, pager)));

    function tab(label, id) {
        var button = h("button", { type: "button", "aria-pressed": String(state.industry_id === id), text: label });
        button.addEventListener("click", function () {
            state.industry_id = id;
            state.page = 1;
            tabs.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", String(b === button)); });
            load();
        });
        return button;
    }

    async function load() {
        var current = ++request;
        grid.style.display = "block";
        V.loading(grid, "Đang tải danh sách công ty...");
        try {
            var data = await V.api("/companies", { auth: false, query: { q: state.q, province_id: state.province_id, industry_id: state.industry_id, page: state.page, page_size: 9 } });
            if (current !== request) return;
            total.textContent = data.total + " doanh nghiệp";
            V.clear(grid);
            if (!data.items.length) V.empty(grid, "Chưa có công ty phù hợp", "Hãy thử từ khóa hoặc bộ lọc khác.");
            else { grid.style.display = ""; data.items.forEach(function (c) { grid.appendChild(V.companyCard(c)); }); }
            V.pagination(pager, data.page, data.total_pages, function (page) { state.page = page; load(); window.scrollTo({ top: 0, behavior: "smooth" }); });
        } catch (error) {
            if (current !== request) return;
            V.clear(pager);
            V.note(grid, error.message, "error");
        }
    }

    input.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(function () { state.q = input.value.trim(); state.page = 1; load(); }, 300);
    });
    province.addEventListener("change", function () { state.province_id = province.value; state.page = 1; load(); });
    tabs.appendChild(tab("Tất cả", ""));
    V.categories().then(function (data) {
        V.fillSelect(province, data.provinces, "Tất cả địa điểm");
        (data.industries || []).slice(0, 6).forEach(function (i) { tabs.appendChild(tab(i.name, String(i.id))); });
    });
    load();
}());
