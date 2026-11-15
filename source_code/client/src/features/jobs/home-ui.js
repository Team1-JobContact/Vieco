/* Trang chủ: ô tìm kiếm, công ty nổi bật và việc làm trending lấy từ API thật. */
(function () {
    "use strict";
    var V = window.Vieco, h = V.h;
    var jobsBox = document.getElementById("jobs-container");
    var filterBox = document.getElementById("jobs-filter");
    var companiesBox = document.getElementById("home-companies");
    var industryId = "";

    document.getElementById("hero-search").appendChild(V.searchForm());

    async function loadJobs() {
        V.loading(jobsBox, "Đang tải việc làm...");
        try {
            var data = await V.api("/jobs", { auth: false, query: { industry_id: industryId, page_size: 6 } });
            V.clear(jobsBox);
            if (!data.items.length) {
                jobsBox.style.display = "block";
                return V.empty(jobsBox, "Chưa có việc làm đang tuyển", "Các tin mới được duyệt sẽ xuất hiện tại đây.");
            }
            jobsBox.style.display = "";
            data.items.forEach(function (job) { jobsBox.appendChild(V.jobCard(job)); });
        } catch (error) {
            jobsBox.style.display = "block";
            V.note(jobsBox, error.message, "error");
        }
    }

    function filterButton(label, id) {
        var button = h("button", { type: "button", "aria-pressed": String(id === industryId), text: label });
        button.addEventListener("click", function () {
            industryId = id;
            filterBox.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", String(b === button)); });
            loadJobs();
        });
        return button;
    }

    async function loadFilters() {
        filterBox.appendChild(filterButton("Tất cả", ""));
        var data = await V.categories();
        (data.industries || []).slice(0, 5).forEach(function (item) { filterBox.appendChild(filterButton(item.name, String(item.id))); });
    }

    async function loadCompanies() {
        try {
            var data = await V.api("/companies", { auth: false, query: { page_size: 3 } });
            V.clear(companiesBox);
            if (!data.items.length) {
                companiesBox.style.display = "block";
                return V.empty(companiesBox, "Chưa có công ty được duyệt", "Doanh nghiệp đã được Vieco xác minh sẽ hiển thị tại đây.");
            }
            data.items.forEach(function (company) { companiesBox.appendChild(V.companyCard(company)); });
        } catch (error) {
            companiesBox.style.display = "block";
            V.note(companiesBox, error.message, "error");
        }
    }

    loadFilters();
    loadJobs();
    loadCompanies();
}());
