/* Danh sách việc làm (PB-021): tìm kiếm, lọc, sắp xếp, phân trang; trạng thái lưu trên URL để chia sẻ được. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var form = document.getElementById("jobs-filter-form");
    var box = document.getElementById("jobs-container");
    var totalNode = document.getElementById("jobs-total");
    var activeBox = document.getElementById("jobs-active");
    var pager = document.getElementById("jobs-pagination");
    var sortSelect = document.getElementById("jobs-sort");
    var params = new URLSearchParams(window.location.search);
    var state = {
        q: params.get("q") || "", industry_id: params.get("industry_id") || "", province_id: params.get("province_id") || "",
        experience_level: params.get("experience_level") || "", employment_type: params.get("employment_type") || "",
        salary_min: params.get("salary_min") || "", salary_max: params.get("salary_max") || "",
        sort: params.get("sort") || "newest", page: Math.max(1, parseInt(params.get("page"), 10) || 1)
    };
    var names = { industry_id: {}, province_id: {}, experience_level: V.EXPERIENCE, employment_type: V.EMPLOYMENT };
    var request = 0;

    function radios(container, name, options) {
        V.clear(container);
        [["", "Tất cả"]].concat(options).forEach(function (option) {
            container.appendChild(h("label", { class: "v-check" },
                h("input", { type: "radio", name: name, value: option[0], checked: String(state[name]) === String(option[0]) }), option[1]));
        });
    }

    function syncUrl() {
        var next = new URLSearchParams();
        Object.keys(state).forEach(function (key) {
            if (state[key] && !(key === "page" && state.page === 1) && !(key === "sort" && state.sort === "newest")) next.set(key, state[key]);
        });
        window.history.replaceState(null, "", window.location.pathname + (next.toString() ? "?" + next : ""));
    }

    function renderActive() {
        V.clear(activeBox);
        function chip(label, reset) {
            activeBox.appendChild(h("span", { class: "v-chip v-chip-lg" }, label,
                h("button", { type: "button", "aria-label": "Bỏ lọc " + label, onclick: function () { reset(); state.page = 1; applyToForm(); load(); } }, V.icon("close", "v-icon-sm"))));
        }
        if (state.q) chip("“" + state.q + "”", function () { state.q = ""; search.input.value = ""; });
        ["industry_id", "province_id", "experience_level", "employment_type"].forEach(function (key) {
            if (state[key]) chip(names[key][state[key]] || state[key], function () { state[key] = ""; });
        });
        if (state.salary_min || state.salary_max) {
            chip((state.salary_min || "0") + " – " + (state.salary_max || "∞") + " triệu", function () { state.salary_min = ""; state.salary_max = ""; });
        }
    }

    function applyToForm() {
        ["industry_id", "province_id", "experience_level", "employment_type"].forEach(function (key) {
            form.querySelectorAll('input[name="' + key + '"]').forEach(function (input) { input.checked = input.value === String(state[key]); });
        });
        form.elements.salary_min.value = state.salary_min;
        form.elements.salary_max.value = state.salary_max;
        sortSelect.value = state.sort;
    }

    async function load() {
        var current = ++request;
        syncUrl();
        renderActive();
        V.loading(box, "Đang tìm việc làm...");
        try {
            var data = await V.api("/jobs", { auth: false, query: {
                q: state.q, industry_id: state.industry_id, province_id: state.province_id,
                experience_level: state.experience_level, employment_type: state.employment_type,
                salary_min: state.salary_min ? Number(state.salary_min) * 1000000 : "",
                salary_max: state.salary_max ? Number(state.salary_max) * 1000000 : "",
                sort: state.sort, page: state.page, page_size: 10
            } });
            if (current !== request) return; // bỏ kết quả của yêu cầu cũ
            totalNode.textContent = String(data.total);
            V.clear(box);
            if (!data.items.length) {
                V.empty(box, "Không tìm thấy việc làm phù hợp", "Hãy thử từ khóa khác hoặc bỏ bớt bộ lọc.");
            } else {
                data.items.forEach(function (job) { box.appendChild(V.jobRow(job)); });
            }
            V.pagination(pager, data.page, data.total_pages, function (page) {
                state.page = page;
                load();
                window.scrollTo({ top: form.getBoundingClientRect().top + window.scrollY - 120, behavior: "smooth" });
            });
        } catch (error) {
            if (current !== request) return;
            totalNode.textContent = "0";
            V.clear(pager);
            V.note(box, error.message, "error");
        }
    }

    var search = V.searchForm({ variant: "v-searchbar-white", q: state.q, province_id: state.province_id, onSubmit: function (values) {
        state.q = values.q;
        state.province_id = values.province_id;
        state.page = 1;
        applyToForm();
        load();
    } });
    document.getElementById("jobs-search").appendChild(search);

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        var data = new FormData(form);
        ["industry_id", "province_id", "experience_level", "employment_type", "salary_min", "salary_max"].forEach(function (key) {
            state[key] = String(data.get(key) || "").trim();
        });
        if (state.salary_min && state.salary_max && Number(state.salary_min) > Number(state.salary_max)) {
            return V.toast("Mức lương tối thiểu phải nhỏ hơn hoặc bằng mức tối đa", true);
        }
        state.page = 1;
        load();
    });
    form.addEventListener("change", function (event) { if (event.target.type === "radio") form.requestSubmit(); });
    form.addEventListener("reset", function () {
        setTimeout(function () {
            ["industry_id", "province_id", "experience_level", "employment_type", "salary_min", "salary_max"].forEach(function (key) { state[key] = ""; });
            state.page = 1;
            applyToForm();
            load();
        });
    });
    sortSelect.addEventListener("change", function () { state.sort = sortSelect.value; state.page = 1; load(); });

    radios(document.getElementById("filter-experience"), "experience_level", Object.keys(V.EXPERIENCE).map(function (k) { return [k, V.EXPERIENCE[k]]; }));
    radios(document.getElementById("filter-employment"), "employment_type", Object.keys(V.EMPLOYMENT).map(function (k) { return [k, V.EMPLOYMENT[k]]; }));
    sortSelect.value = state.sort;
    form.elements.salary_min.value = state.salary_min;
    form.elements.salary_max.value = state.salary_max;
    V.categories().then(function (data) {
        (data.industries || []).forEach(function (i) { names.industry_id[i.id] = i.name; });
        (data.provinces || []).forEach(function (p) { names.province_id[p.id] = p.name; });
        radios(document.getElementById("filter-industry"), "industry_id", (data.industries || []).map(function (i) { return [i.id, i.name]; }));
        radios(document.getElementById("filter-province"), "province_id", (data.provinces || []).map(function (p) { return [p.id, p.name]; }));
        renderActive();
    });
    load();
}());
