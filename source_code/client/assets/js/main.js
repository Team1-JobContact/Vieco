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

function handleSearch() {
    const keyword = document.getElementById("keyword-input").value;
    alert(`Tìm kiếm từ khóa: ${keyword}`);
}
