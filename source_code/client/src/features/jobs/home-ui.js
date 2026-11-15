const API_BASE_URL = window.ViecoAuthApi
    ? window.ViecoAuthApi.getApiBaseUrl()
    : "http://127.0.0.1:8000/api/v1";

function renderLoggedOutNav(container) {
    container.innerHTML =
        '<a href="pages/login.html" class="btn btn-outline">Đăng nhập</a>' +
        '<a href="pages/register.html" class="btn btn-primary">Đăng ký</a>';
}

function renderLoggedInNav(container, user, token) {
    var Api = window.ViecoAuthApi;
    container.innerHTML = "";

    var pill = document.createElement("span");
    pill.className = "nav-user-pill";

    var nameSpan = document.createElement("span");
    nameSpan.textContent = user.full_name;
    pill.appendChild(nameSpan);

    var roleSpan = document.createElement("span");
    roleSpan.className = "nav-role-tag";
    roleSpan.textContent = Api ? Api.getRoleLabel(user.role) : user.role;
    pill.appendChild(roleSpan);

    var logoutBtn = document.createElement("button");
    logoutBtn.type = "button";
    logoutBtn.className = "btn btn-outline";
    logoutBtn.id = "nav-logout-btn";
    logoutBtn.textContent = "Đăng xuất";

    logoutBtn.addEventListener("click", async function () {
        logoutBtn.disabled = true;
        logoutBtn.textContent = "Đang đăng xuất...";
        try {
            if (Api && token) {
                await Api.logoutUser(token);
            }
        } catch (_) {
            // Clear session even if network or token check fails
        } finally {
            if (Api) Api.clearAuthSession();
            renderLoggedOutNav(container);
        }
    });

    container.appendChild(pill);
    if (user.role === "EMPLOYER") {
        var employerLink = document.createElement("a");
        employerLink.href = "pages/employer.html";
        employerLink.className = "btn btn-primary";
        employerLink.textContent = "Không gian tuyển dụng";
        container.appendChild(employerLink);
    }
    container.appendChild(logoutBtn);
}

async function syncNavbarAuthState() {
    var Api = window.ViecoAuthApi;
    var container = document.getElementById("nav-auth-actions");
    if (!Api || !container) return;

    var token = Api.getAuthToken();
    if (!token) {
        renderLoggedOutNav(container);
        return;
    }

    var cachedUser = Api.getStoredUser();
    if (cachedUser) {
        renderLoggedInNav(container, cachedUser, token);
    }

    try {
        var user = await Api.fetchCurrentUser(token);
        Api.saveAuthSession(token, user, Boolean(window.localStorage.getItem("vieco_access_token")));
        renderLoggedInNav(container, user, token);
    } catch (err) {
        if (err && err.status === 401) {
            Api.clearAuthSession();
            renderLoggedOutNav(container);
        }
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    var toggle = document.getElementById("nav-toggle");
    var menu = document.getElementById("nav-menu");
    if (toggle && menu) {
        toggle.addEventListener("click", () => {
            var expanded = menu.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        });
    }

    syncNavbarAuthState();

    const statusBadge = document.getElementById("api-status");
    if (!statusBadge) return;
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        await response.json();

        if (response.ok) {
            statusBadge.innerText = "API: Hoạt động";
            statusBadge.style.background = "#dcfce7";
            statusBadge.style.color = "#166534";
        }
    } catch (error) {
        statusBadge.innerText = "API: Mất kết nối";
        statusBadge.style.background = "#fee2e2";
        statusBadge.style.color = "#991b1b";
    }
});

let jobsRequest = 0;
let jobsPage = 1;
let jobsQuery = "";

async function loadJobs(page) {
    const request = ++jobsRequest;
    const container = document.getElementById("jobs-container");
    const pagination = document.getElementById("jobs-pagination");
    container.textContent = "Đang tải việc làm...";
    pagination.replaceChildren();
    try {
        const data = await window.ViecoJobsApi.list(jobsQuery, page);
        if (request !== jobsRequest) return;
        jobsPage = data.page;
        container.replaceChildren();
        if (!data.items.length) container.textContent = "Chưa có tin tuyển dụng phù hợp";
        data.items.forEach(function (job) {
            const card = document.createElement("article");
            card.className = "job-card";
            const title = document.createElement("h4");
            title.className = "job-title";
            title.textContent = job.title;
            const company = document.createElement("p");
            company.className = "company-name";
            company.textContent = job.company_name;
            const province = document.createElement("p");
            province.textContent = job.province_name || "Chưa cập nhật địa điểm";
            const details = document.createElement("div");
            details.hidden = true;
            const button = document.createElement("button");
            button.className = "btn btn-outline";
            button.textContent = "Xem chi tiết";
            button.type = "button";
            button.setAttribute("aria-expanded", "false");
            button.addEventListener("click", async function () {
                if (!details.hidden) {
                    details.hidden = true;
                    button.setAttribute("aria-expanded", "false");
                    return;
                }
                button.disabled = true;
                try {
                    const item = await window.ViecoJobsApi.get(job.id);
                    details.replaceChildren();
                    [item.description, item.requirements, item.benefits].filter(Boolean).forEach(function (text) {
                        const paragraph = document.createElement("p");
                        paragraph.textContent = text;
                        details.appendChild(paragraph);
                    });
                    details.hidden = false;
                    button.setAttribute("aria-expanded", "true");
                } catch (error) {
                    details.textContent = error.message;
                    details.hidden = false;
                } finally { button.disabled = false; }
            });
            card.append(title, company, province, button, details);
            container.appendChild(card);
        });
        const label = document.createElement("span");
        label.textContent = "Trang " + data.page + "/" + Math.max(1, data.total_pages);
        const prev = document.createElement("button");
        prev.type = "button"; prev.className = "btn btn-outline"; prev.textContent = "Trang trước";
        prev.disabled = data.page <= 1;
        prev.addEventListener("click", () => loadJobs(jobsPage - 1));
        const next = document.createElement("button");
        next.type = "button"; next.className = "btn btn-outline"; next.textContent = "Trang sau";
        next.disabled = data.page >= data.total_pages;
        next.addEventListener("click", () => loadJobs(jobsPage + 1));
        pagination.append(prev, label, next);
    } catch (error) {
        if (request === jobsRequest) container.textContent = error.message || "Không kết nối được máy chủ";
    }
}

function handleSearch() {
    jobsQuery = document.getElementById("keyword-input").value.trim();
    loadJobs(1);
}

document.addEventListener("DOMContentLoaded", function () {
    loadJobs(1);
    document.getElementById("keyword-input").addEventListener("keydown", function (event) {
        if (event.key === "Enter") { event.preventDefault(); handleSearch(); }
    });
});
