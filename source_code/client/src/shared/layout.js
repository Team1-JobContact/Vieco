/* Khung trang dùng chung theo Figma: header, menu, bảng tìm kiếm, footer và các tiện ích giao diện.
   Mọi dữ liệu từ API đều được chèn bằng textContent để tránh XSS. */
(function () {
    "use strict";

    var Auth = window.ViecoAuthApi;
    var script = document.currentScript;
    var ROOT = script && script.src ? script.src.replace(/src\/shared\/layout\.js.*$/, "") : (document.body && document.body.dataset.root) || "";

    function url(path) { return ROOT + path; }

    // ---------- DOM ----------
    function h(tag, props) {
        var node = document.createElement(tag);
        Object.keys(props || {}).forEach(function (key) {
            var value = props[key];
            if (value === null || value === undefined || value === false) return;
            if (key === "class") node.className = value;
            else if (key === "text") node.textContent = value;
            else if (key.slice(0, 2) === "on") node.addEventListener(key.slice(2), value);
            else if (key === "hidden" || key === "disabled" || key === "checked" || key === "selected" || key === "required") node[key] = Boolean(value);
            else if (key === "value") node.value = value;
            else node.setAttribute(key, value === true ? "" : String(value));
        });
        for (var i = 2; i < arguments.length; i++) append(node, arguments[i]);
        return node;
    }
    function append(node, child) {
        if (child === null || child === undefined || child === false) return;
        if (Array.isArray(child)) child.forEach(function (c) { append(node, c); });
        else node.appendChild(child.nodeType ? child : document.createTextNode(String(child)));
    }
    function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); return node; }

    var ICONS = {
        arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
        out: '<path d="M7 17 17 7M9 7h8v8"/>',
        close: '<path d="M6 6l12 12M18 6 6 18"/>',
        search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
        pin: '<path d="M19 10c0 5-7 11-7 11s-7-6-7-11a7 7 0 0 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/>',
        brief: '<rect x="3" y="7" width="18" height="13" rx="1"/><path d="M9 7V4h6v3M9 7v13M15 7v13"/>',
        users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
        user: '<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>',
        clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        bookmark: '<path d="M6 3h12v18l-6-4-6 4V3Z"/>',
        check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
        plus: '<path d="M12 5v14M5 12h14"/>',
        left: '<path d="m14 6-6 6 6 6"/>',
        right: '<path d="m10 6 6 6-6 6"/>',
        bell: '<path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 15 6 9ZM10 20a2 2 0 0 0 4 0"/>',
        file: '<path d="M6 3h8l4 4v14H6V3Z"/><path d="M14 3v4h4"/>',
        upload: '<path d="M12 15V4M7.5 8.5 12 4l4.500 4.5M4 15v5h16v-5"/>',
        send: '<path d="M21 3 10 14M21 3l-7 18-4-7-7-4 18-7Z"/>',
        eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
        mail: '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="m3 7 9 6 9-6"/>',
        phone: '<rect x="7" y="2.500" width="10" height="19" rx="1.500"/><path d="M11 18h2"/>',
        edit: '<path d="M4 20h4L19 9l-4-4L4 16v4ZM13.500 6.500l4 4"/>',
        globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
        trend: '<path d="m3 17 6-6 4 4 8-8M15 7h6v6"/>',
        trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
        download: '<path d="M12 4v11M7.500 10.500 12 15l4.500-4.500M4 20h16"/>',
        shield: '<path d="M12 3 4 6v6c0 5 3.500 8 8 9 4.500-1 8-4 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/>'
    };
    function icon(name, cls) {
        var span = document.createElement("span");
        span.innerHTML = '<svg class="v-icon ' + (cls || "") + '" viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[name] || "") + "</svg>";
        return span.firstChild;
    }

    // ---------- API ----------
    function errorMessage(status, body) {
        var detail = body && body.detail;
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail) && detail.length) {
            return String(detail[0].msg || "Dữ liệu không hợp lệ").replace(/^Value error,\s*/, "");
        }
        if (status === 401) return "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại";
        if (status === 403) return "Bạn không có quyền thực hiện thao tác này";
        if (status === 404) return "Không tìm thấy dữ liệu";
        return "Có lỗi xảy ra, vui lòng thử lại";
    }

    async function api(path, options) {
        options = options || {};
        var headers = {};
        var token = Auth.getAuthToken();
        if (token && options.auth !== false) headers.Authorization = "Bearer " + token;
        var body;
        if (options.formData) body = options.formData;
        else if (options.body !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(options.body); }
        var query = "";
        if (options.query) {
            var params = new URLSearchParams();
            Object.keys(options.query).forEach(function (key) {
                var value = options.query[key];
                if (value !== null && value !== undefined && value !== "") params.set(key, value);
            });
            query = params.toString() ? "?" + params.toString() : "";
        }
        var response;
        try {
            response = await fetch(Auth.getApiBaseUrl() + path + query, { method: options.method || "GET", headers: headers, body: body });
        } catch (_) {
            // Trình duyệt cũng báo lỗi mạng khi backend trả lỗi 500 ở chế độ DEBUG (thiếu header CORS).
            throw new Error("Không nhận được phản hồi từ máy chủ. Kiểm tra backend đang chạy ở cổng 8000; nếu đang chạy, xem lỗi trong terminal backend (thường do chưa chạy alembic upgrade head).");
        }
        if (options.blob && response.ok) return response.blob();
        var data = null;
        if (response.status !== 204) { try { data = await response.json(); } catch (_) { data = null; } }
        if (!response.ok) {
            if (response.status === 401 && token && options.auth !== false) {
                Auth.clearAuthSession();
                goLogin();
            }
            var error = new Error(errorMessage(response.status, data));
            error.status = response.status;
            throw error;
        }
        return data;
    }

    /** Tải tệp cần xác thực (CV) rồi mở hộp lưu của trình duyệt. */
    async function download(path, fileName) {
        var blob = await api(path, { blob: true });
        var link = h("a", { href: URL.createObjectURL(blob), download: fileName || "cv" });
        document.body.appendChild(link);
        link.click();
        setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 1000);
    }

    function goLogin() {
        var here = window.location.pathname + window.location.search + window.location.hash;
        window.location.href = url("pages/login.html") + "?redirect=" + encodeURIComponent(here);
    }

    var userPromise = null;
    function currentUser() {
        if (!userPromise) {
            var token = Auth.getAuthToken();
            userPromise = !token ? Promise.resolve(null) : Auth.fetchCurrentUser(token).catch(function () {
                Auth.clearAuthSession();
                return null;
            });
        }
        return userPromise;
    }

    /** Trả về user nếu đúng vai trò; chưa đăng nhập thì chuyển tới trang đăng nhập; sai vai trò thì trả null. */
    async function requireRole(roles, container) {
        var user = await currentUser();
        if (!user) { goLogin(); return null; }
        if (roles.indexOf(user.role) === -1) {
            if (container) {
                clear(container).appendChild(h("div", { class: "v-empty" },
                    h("h3", { text: "Bạn không có quyền truy cập trang này" }),
                    h("p", { text: "Trang này dành cho vai trò khác. Vai trò của bạn: " + roleLabel(user.role) + "." }),
                    h("a", { class: "v-btn v-btn-primary v-btn-sm", href: url("index.html"), text: "Về trang chủ" })));
            }
            return null;
        }
        return user;
    }

    var categoriesPromise = null;
    function categories() {
        if (!categoriesPromise) {
            categoriesPromise = api("/categories", { auth: false }).catch(function () {
                categoriesPromise = null;
                return { industries: [], provinces: [], skills: [] };
            });
        }
        return categoriesPromise;
    }
    function fillSelect(select, items, placeholder) {
        clear(select);
        if (placeholder !== undefined) select.appendChild(h("option", { value: "", text: placeholder }));
        (items || []).forEach(function (item) { select.appendChild(h("option", { value: item.id, text: item.name })); });
    }

    // ---------- Định dạng ----------
    var EXPERIENCE = { NONE: "Chưa có kinh nghiệm", UNDER_1: "Dưới 1 năm", FROM_1_TO_3: "1 – 3 năm", FROM_3_TO_5: "3 – 5 năm", OVER_5: "Trên 5 năm" };
    var EMPLOYMENT = { FULL_TIME: "Toàn thời gian", PART_TIME: "Bán thời gian", INTERNSHIP: "Thực tập", CONTRACT: "Hợp đồng", FREELANCE: "Tự do" };
    var APP_STATUS = {
        NEW: ["Đã gửi", ""], VIEWED: ["Đang xem xét", "v-badge-sand"], INTERVIEW: ["Mời phỏng vấn", "v-badge-blue"],
        ACCEPTED: ["Trúng tuyển", "v-badge-green"], REJECTED: ["Chưa phù hợp", "v-badge-outline"], WITHDRAWN: ["Đã rút", "v-badge-outline"]
    };
    var JOB_STATUS = {
        DRAFT: ["Bản nháp", "v-badge-outline"], PENDING: ["Chờ duyệt", "v-badge-sand"], APPROVED: ["Đang hiển thị", "v-badge-green"],
        REJECTED: ["Bị từ chối", "v-badge-red"], CLOSED: ["Đã đóng", ""], EXPIRED: ["Hết hạn", ""]
    };
    var COMPANY_STATUS = { PENDING: ["Chờ duyệt", "v-badge-sand"], APPROVED: ["Đã duyệt", "v-badge-green"], REJECTED: ["Bị từ chối", "v-badge-red"] };
    var ROLES = { CANDIDATE: "Ứng viên", EMPLOYER: "Nhà tuyển dụng", ADMIN: "Quản trị viên" };
    function roleLabel(role) { return ROLES[role] || role; }
    function badge(map, status) {
        var item = map[status] || [status, ""];
        return h("span", { class: "v-badge " + item[1], text: item[0] });
    }

    function million(value) {
        var m = value / 1000000;
        return (Math.round(m * 10) / 10).toLocaleString("vi-VN");
    }
    function salary(job) {
        var min = job.salary_min, max = job.salary_max;
        if (!min && !max) return "Thỏa thuận";
        if (min && max) return min === max ? million(min) + " triệu" : million(min) + " – " + million(max) + " triệu";
        return min ? "Từ " + million(min) + " triệu" : "Đến " + million(max) + " triệu";
    }
    function parseDate(value) {
        if (!value) return null;
        // API trả giờ UTC không kèm múi giờ; ngày thuần (YYYY-MM-DD) giữ nguyên theo lịch.
        var text = String(value);
        var date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(text) ? text + "T00:00:00" : (/[zZ]|[+-]\d{2}:\d{2}$/.test(text) ? text : text + "Z"));
        return isNaN(date.getTime()) ? null : date;
    }
    function date(value) {
        var d = parseDate(value);
        return d ? d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" }) : "—";
    }
    function ago(value) {
        var d = parseDate(value);
        if (!d) return "";
        var minutes = Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
        if (minutes < 1) return "Vừa xong";
        if (minutes < 60) return minutes + " phút trước";
        if (minutes < 1440) return Math.round(minutes / 60) + " giờ trước";
        if (minutes < 43200) return Math.round(minutes / 1440) + " ngày trước";
        return date(value);
    }
    function initials(name) {
        var parts = String(name || "").trim().split(/\s+/).filter(Boolean);
        return parts.slice(-2).map(function (p) { return p.charAt(0).toUpperCase(); }).join("") || "V";
    }
    function shortName(name) {
        var parts = String(name || "").trim().split(/\s+/).filter(Boolean);
        return parts.slice(-2).join(" ");
    }
    var BRAND_COLORS = ["#176b9c", "#c15f21", "#bd3038", "#1a5276", "#a03472", "#1f4f9c", "#2f6b4f"];
    function brandColor(name) {
        var sum = 0, text = String(name || "");
        for (var i = 0; i < text.length; i++) sum = (sum + text.charCodeAt(i) * (i + 1)) % 9973;
        return BRAND_COLORS[sum % BRAND_COLORS.length];
    }
    /** Tên ngắn hiển thị như logo chữ trong Figma (FPT, VNG, TCB). */
    function brand(name) {
        var words = String(name || "").replace(/^(công ty|cty)\s+(cổ phần|tnhh|cp)?\s*/i, "").trim().split(/\s+/).filter(Boolean);
        if (!words.length) return "V";
        if (words[0].length <= 6) return words[0].toUpperCase();
        return words.slice(0, 3).map(function (w) { return w.charAt(0); }).join("").toUpperCase();
    }
/** Đường dẫn ảnh do API trả về (/media/...) -> URL đầy đủ; chỉ nhận đường dẫn nội bộ đúng mẫu. */
    function media(path) {
        return /^\/media\/company\/[0-9a-f]{32}\.(jpg|png|webp)$/.test(String(path || "")) ? Auth.getApiBaseUrl() + path : null;
    }
    /** Ô logo: dùng ảnh công ty tự tải lên, nếu chưa có thì hiển thị tên viết tắt. */
    function logo(name, size, logoUrl) {
        var src = media(logoUrl);
        if (src) return h("span", { class: "v-logo v-logo-img " + (size || "") }, h("img", { src: src, alt: "Logo " + (name || "công ty"), loading: "lazy" }));
        var box = h("span", { class: "v-logo " + (size || ""), text: brand(name), "aria-hidden": "true" });
        box.style.color = brandColor(name);
        return box;
    }
    /** Ảnh bìa công ty tự tải lên; chưa có thì trả về khung trống mang tên công ty (không dùng ảnh mặc định). */
    function coverImage(company, cls) {
        var src = media(company.cover_url);
        if (src) return h("img", { class: cls || "photo", src: src, alt: "Ảnh bìa " + company.name, loading: "lazy" });
        var box = h("div", { class: "v-photo-empty " + (cls || "photo"), "aria-hidden": "true", text: brand(company.name) });
        box.style.color = brandColor(company.name);
        return box;
    }
    /** Nhãn hiển thị cho liên kết: link dài thì chỉ hiện "Fanpage" (mạng xã hội) hoặc "Website". */
    var SOCIAL_HOST = /(^|\.)(facebook\.com|fb\.com|fb\.me|instagram\.com|tiktok\.com|linkedin\.com|zalo\.me|youtube\.com|x\.com|twitter\.com)$/i;
    function linkInfo(value) {
        var text = String(value || "").trim();
        if (!/^https?:\/\//i.test(text)) return null;
        var host;
        try { host = new URL(text).hostname; } catch (_) { return null; }
        var social = SOCIAL_HOST.test(host);
        var shown = text.replace(/^https?:\/\/(www\.)?/i, "").replace(/\/$/, "");
        return { href: text, social: social, kind: social ? "Fanpage" : "Website", label: shown.length > 32 ? (social ? "Fanpage" : "Website") : shown };
    }
    function externalLink(value, cls) {
        var info = linkInfo(value);
        if (!info) return null;
        return h("a", { class: cls || "v-link", href: info.href, target: "_blank", rel: "noopener noreferrer", title: info.href, text: info.label });
    }
    function lines(text) {
        return String(text || "").split(/\r?\n/).map(function (l) { return l.replace(/^\s*[-•–*]\s*/, "").trim(); }).filter(Boolean);
    }
    function prose(text) {
        var items = lines(text);
        if (!items.length) return h("p", { class: "v-muted", text: "Chưa có thông tin." });
        if (items.length === 1) return h("div", { class: "v-prose" }, h("p", { text: items[0] }));
        return h("ul", { class: "v-prose" }, items.map(function (l) { return h("li", { text: l }); }));
    }

    // ---------- Thông báo nhanh ----------
    var toastTimer = null;
    function toast(message, isError) {
        var old = document.querySelector(".v-toast");
        if (old) old.remove();
        var node = h("div", { class: "v-toast" + (isError ? " v-toast-error" : ""), role: "status", text: message });
        document.body.appendChild(node);
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { node.remove(); }, 4000);
    }
    function note(container, message, kind) {
        clear(container);
        if (message) container.appendChild(h("div", { class: "v-note " + (kind ? "v-note-" + kind : ""), role: kind === "error" ? "alert" : "status", text: message }));
    }
    function loading(container, text) { clear(container).appendChild(h("p", { class: "v-loading", text: text || "Đang tải..." })); }
    function empty(container, title, text, action) {
        clear(container).appendChild(h("div", { class: "v-empty" }, h("h3", { text: title }), text && h("p", { text: text }), action));
    }

    // ---------- Việc đã lưu ----------
    var savedIds = null;
    async function loadSaved() {
        if (savedIds) return savedIds;
        savedIds = new Set();
        var user = await currentUser();
        if (user && user.role === "CANDIDATE") {
            try {
                (await api("/saved-jobs")).items.forEach(function (job) { savedIds.add(job.id); });
            } catch (_) { /* không chặn trang nếu lỗi */ }
        }
        return savedIds;
    }
    function saveButton(job) {
        var button = h("button", { type: "button", class: "v-save", "aria-label": "Lưu việc " + job.title, "aria-pressed": "false" }, icon("bookmark"));
        function paint(saved) {
            button.classList.toggle("is-saved", saved);
            button.setAttribute("aria-pressed", String(saved));
        }
        loadSaved().then(function (set) { paint(set.has(job.id)); });
        button.addEventListener("click", async function (event) {
            event.preventDefault();
            var user = await currentUser();
            if (!user) return goLogin();
            if (user.role !== "CANDIDATE") return toast("Chỉ tài khoản ứng viên mới lưu được việc làm", true);
            var set = await loadSaved(), saved = set.has(job.id);
            try {
                await api("/saved-jobs/" + job.id, { method: saved ? "DELETE" : "PUT" });
                if (saved) set.delete(job.id); else set.add(job.id);
                paint(!saved);
                toast(saved ? "Đã bỏ lưu việc làm" : "Đã lưu việc làm");
                document.dispatchEvent(new CustomEvent("vieco:saved-changed"));
            } catch (error) { toast(error.message, true); }
        });
        return button;
    }

    // ---------- Thẻ việc làm ----------
    function jobUrl(id) { return url("pages/job.html") + "?id=" + encodeURIComponent(id); }
    function companyUrl(id) { return url("pages/company.html") + "?id=" + encodeURIComponent(id); }
    function jobFacts(job) {
        return [job.province_name, EXPERIENCE[job.experience_level]].filter(Boolean).join("   ·   ");
    }
    function jobCard(job) {
        var brandNode = h("p", { class: "v-job-brand", text: brand(job.company_name) });
        brandNode.style.color = brandColor(job.company_name);
        return h("article", { class: "v-job-card" },
            brandNode,
            h("p", { class: "v-job-company", text: job.company_name || "" }),
            saveButton(job),
            h("h3", { class: "v-job-title" }, h("a", { href: jobUrl(job.id), text: job.title })),
            h("p", { class: "v-job-salary", text: salary(job) }),
            h("p", { class: "v-job-facts", text: jobFacts(job) }),
            h("div", { class: "v-job-foot" },
                h("span", { text: EMPLOYMENT[job.employment_type] || "" }),
                h("span", { class: "v-job-apply", text: "Ứng tuyển  ↗" })));
    }
    function jobRow(job) {
        var chips = (job.skills || []).slice(0, 3).map(function (s) { return h("span", { class: "v-chip", text: s.name }); });
        if (EMPLOYMENT[job.employment_type]) chips.push(h("span", { class: "v-chip", text: EMPLOYMENT[job.employment_type] }));
        return h("article", { class: "v-job-row" },
            logo(job.company_name, "v-logo-md", job.company_logo_url),
            h("div", {},
                h("h3", {}, h("a", { href: jobUrl(job.id), text: job.title })),
                h("p", { class: "company", text: job.company_name || "" }),
                h("div", { class: "v-meta" },
                    job.province_name && h("span", {}, icon("pin", "v-icon-sm"), job.province_name),
                    EXPERIENCE[job.experience_level] && h("span", {}, icon("brief", "v-icon-sm"), EXPERIENCE[job.experience_level]),
                    h("span", {}, icon("clock", "v-icon-sm"), ago(job.published_at || job.created_at))),
                h("div", { class: "v-chips" }, chips)),
            h("div", { class: "v-job-row-side" },
                saveButton(job),
                h("span", { class: "salary", text: salary(job) }),
                h("span", { class: "v-job-apply", text: "Ứng tuyển  ↗" })));
    }

    function companyCard(company) {
        var name = h("p", { class: "name", text: brand(company.name) });
        name.style.color = brandColor(company.name);
        return h("article", { class: "v-company-card" },
            coverImage(company),
            h("div", { class: "body" },
                h("div", { class: "top" }, name, h("a", { class: "v-link v-small", href: companyUrl(company.id), "aria-label": "Xem công ty " + company.name, text: "Xem công ty ↗" })),
                h("p", { class: "industry", text: company.name }),
                h("p", { class: "place", text: [company.industry_name, company.province_name].filter(Boolean).join(" · ") || "Đang cập nhật" }),
                h("div", { class: "foot" }, h("span", {}, icon("brief", "v-icon-sm"), (company.open_jobs || 0) + " vị trí đang tuyển"))));
    }

    function pagination(container, page, totalPages, onChange) {
        clear(container);
        if (!totalPages || totalPages <= 1) return;
        function button(label, target, opts) {
            opts = opts || {};
            var node = h("button", { type: "button", "aria-label": opts.label || "Trang " + target, disabled: opts.disabled,
                "aria-current": target === page && !opts.nav ? "page" : null }, label);
            node.addEventListener("click", function () { if (target !== page) onChange(target); });
            return node;
        }
        container.appendChild(button(icon("left", "v-icon-sm"), page - 1, { nav: true, disabled: page <= 1, label: "Trang trước" }));
        var shown = [1, page - 1, page, page + 1, totalPages].filter(function (p, i, all) {
            return p >= 1 && p <= totalPages && all.indexOf(p) === i;
        }).sort(function (a, b) { return a - b; });
        shown.forEach(function (p, i) {
            if (i && p - shown[i - 1] > 1) container.appendChild(h("span", { class: "v-muted", text: "…" }));
            container.appendChild(button(String(p), p));
        });
        container.appendChild(button(icon("right", "v-icon-sm"), page + 1, { nav: true, disabled: page >= totalPages, label: "Trang sau" }));
    }

    // ---------- Modal ----------
    function modal(content, options) {
        options = options || {};
        var previous = document.activeElement;
        var box = h("div", { class: "v-modal " + (options.small ? "v-modal-sm" : ""), role: "dialog", "aria-modal": "true", "aria-label": options.label || "Hộp thoại" });
        var scrim = h("div", { class: "v-modal-scrim" }, box);
        function close() {
            scrim.remove();
            document.removeEventListener("keydown", onKey);
            document.body.style.overflow = "";
            if (previous && previous.focus) previous.focus();
            if (options.onClose) options.onClose();
        }
        function onKey(event) { if (event.key === "Escape") close(); }
        if (!options.small) box.appendChild(h("button", { type: "button", class: "v-modal-close", "aria-label": "Đóng", onclick: close }, icon("close", "v-icon-lg")));
        append(box, typeof content === "function" ? content(close) : content);
        scrim.addEventListener("mousedown", function (event) { if (event.target === scrim) close(); });
        document.addEventListener("keydown", onKey);
        document.body.appendChild(scrim);
        document.body.style.overflow = "hidden";
        var focusable = box.querySelector("input, select, textarea, button, a");
        if (focusable) focusable.focus();
        return close;
    }
    function confirmDialog(title, message, confirmText, danger) {
        return new Promise(function (resolve) {
            var done = false;
            modal(function (close) {
                return [
                    h("h2", { class: "v-mt-0", text: title }),
                    h("p", { class: "v-lead", text: message }),
                    h("div", { class: "v-flex v-mt-3", style: "justify-content:center" },
                        h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Hủy", onclick: close }),
                        h("button", { type: "button", class: "v-btn v-btn-sm " + (danger ? "v-btn-danger" : "v-btn-primary"), text: confirmText || "Xác nhận",
                            onclick: function () { done = true; close(); } }))
                ];
            }, { small: true, label: title, onClose: function () { resolve(done); } });
        });
    }

    // ---------- Header / Menu / Tìm kiếm / Footer ----------
    var NAV = [
        ["index.html", "Trang chủ", "Chạm cơ hội, mở tương lai"],
        ["pages/jobs.html", "Việc làm", "Khám phá các vị trí đang tuyển"],
        ["pages/companies.html", "Công ty", "Tìm hiểu môi trường làm việc"],
        ["pages/cv-library.html", "Thư viện CV", "Mẫu CV thanh lịch, hiện đại, tối giản"],
        ["pages/for-employers.html", "Dành cho nhà tuyển dụng", "Đăng tin và tìm ứng viên phù hợp"],
        ["pages/contact.html", "Liên hệ", "Kết nối với đội ngũ Vieco"]
    ];
    function accountLinks(user) {
        var links = {
            CANDIDATE: [["pages/profile.html", "Hồ sơ của tôi"], ["pages/profile.html#applications", "Việc đã ứng tuyển"], ["pages/profile.html#saved", "Việc đã lưu"], ["pages/profile.html#cvs", "CV của tôi"]],
            EMPLOYER: [["pages/employer-jobs.html", "Quản lý tin và ứng viên"], ["pages/employer.html", "Hồ sơ công ty"], ["pages/company-media.html", "Hình ảnh công ty"], ["pages/employer.html#job", "Đăng tin mới"]],
            ADMIN: [["pages/admin.html", "Trang quản trị"], ["pages/admin.html#jobs", "Duyệt tin tuyển dụng"]]
        }[user.role] || [];
        return links.concat([["pages/notifications.html", "Thông báo"]]);
    }
    async function logout() {
        var token = Auth.getAuthToken();
        try { if (token) await Auth.logoutUser(token); } catch (_) { /* vẫn xóa phiên phía client */ }
        Auth.clearAuthSession();
        window.location.href = url("index.html");
    }

    function isCurrent(path) {
        var here = window.location.pathname.replace(/\/$/, "/index.html");
        return here.slice(-path.length) === path && (path !== "index.html" || !/\/pages\//.test(here));
    }

    function renderHeader(mount) {
        var actions = h("div", { class: "v-flex", style: "gap:24px;flex-wrap:nowrap" },
            h("a", { class: "v-btn v-btn-primary v-login-btn", href: url("pages/login.html"), text: "Đăng nhập" }));
        var header = h("header", { class: "v-header" },
            h("div", { class: "v-header-inner" },
                h("div", { class: "v-header-left" },
                    h("a", { class: "v-mark", href: url("index.html"), "aria-label": "Vieco – Trang chủ" },
                        h("img", { src: url("src/assets/images/brand/vieco-mark.png"), alt: "", width: "75", height: "48" })),
                    h("button", { type: "button", class: "v-head-btn v-menu-btn", "aria-label": "Menu", "aria-haspopup": "dialog", onclick: openDrawer },
                        h("img", { src: url("src/assets/images/icons/menu.svg"), alt: "" }), h("span", { class: "v-hide-sm", text: "Menu" }))),
                h("a", { class: "v-wordmark", href: url("index.html"), text: "VIECO" }),
                h("div", { class: "v-header-right" },
                    h("a", { class: "v-head-btn v-hide-md", href: url("pages/contact.html"), text: "Liên hệ" }),
                    h("button", { type: "button", class: "v-head-btn", "aria-haspopup": "dialog", onclick: openSearch },
                        h("img", { src: url("src/assets/images/icons/search.svg"), alt: "" }), h("span", { class: "v-hide-md", text: "Tìm kiếm" })),
                    actions)));
        clear(mount).appendChild(header);

        currentUser().then(function (user) {
            if (!user) return;
            var menu = h("div", { class: "v-user-menu", hidden: true },
                h("div", { class: "v-user-menu-head" }, h("strong", { text: user.full_name }), h("span", { class: "v-small v-muted", text: roleLabel(user.role) })),
                accountLinks(user).map(function (l) { return h("a", { href: url(l[0]), text: l[1] }); }),
                h("button", { type: "button", text: "Đăng xuất", onclick: logout }));
            var toggle = h("button", { type: "button", class: "v-btn v-btn-primary v-login-btn", "aria-haspopup": "menu", "aria-expanded": "false", text: user.role === "ADMIN" ? "Quản trị" : shortName(user.full_name) });
            toggle.addEventListener("click", function (event) {
                event.stopPropagation();
                menu.hidden = !menu.hidden;
                toggle.setAttribute("aria-expanded", String(!menu.hidden));
            });
            document.addEventListener("click", function (event) {
                if (!menu.contains(event.target)) { menu.hidden = true; toggle.setAttribute("aria-expanded", "false"); }
            });
            var count = h("span", { class: "v-bell-count", hidden: true });
            var bell = h("a", { class: "v-bell", href: url("pages/notifications.html"), "aria-label": "Thông báo" }, icon("bell", "v-icon-lg"), count);
            clear(actions);
            append(actions, [bell, h("div", { class: "v-user" }, toggle, menu)]);
            refreshUnread = function () {
                api("/notifications", { query: { page_size: 1 } }).then(function (data) {
                    var n = data.unread_count || 0;
                    count.hidden = n === 0;
                    count.textContent = n > 99 ? "99+" : String(n);
                    bell.setAttribute("aria-label", "Thông báo, " + n + " chưa đọc");
                }).catch(function () {});
            };
            refreshUnread();
        });
    }
    var refreshUnread = function () {};

    var overlay = null;
    function closeOverlay() {
        if (!overlay) return;
        var current = overlay;
        overlay = null;
        current.panel.classList.remove("is-open");
        current.scrim.remove();
        document.removeEventListener("keydown", current.onKey);
        document.body.style.overflow = "";
        setTimeout(function () { current.panel.remove(); }, 250);
        if (current.opener && current.opener.focus) current.opener.focus();
    }
    function showOverlay(panel) {
        closeOverlay();
        var scrim = h("div", { class: "v-scrim", onclick: closeOverlay });
        var onKey = function (event) { if (event.key === "Escape") closeOverlay(); };
        overlay = { panel: panel, scrim: scrim, onKey: onKey, opener: document.activeElement };
        document.body.appendChild(scrim);
        document.body.appendChild(panel);
        document.body.style.overflow = "hidden";
        document.addEventListener("keydown", onKey);
        requestAnimationFrame(function () { panel.classList.add("is-open"); });
    }

    function openDrawer() {
        var foot = h("div", { class: "v-drawer-foot" });
        var drawer = h("div", { class: "v-drawer", role: "dialog", "aria-modal": "true", "aria-label": "Menu điều hướng" },
            h("div", { class: "v-drawer-head" },
                h("a", { class: "v-mark", href: url("index.html"), text: "V" }),
                h("button", { type: "button", class: "v-close", onclick: closeOverlay }, "Đóng", icon("close", "v-icon-lg"))),
            h("p", { class: "v-eyebrow", text: "Điều hướng" }),
            h("nav", { class: "v-drawer-nav", "aria-label": "Chính" }, NAV.map(function (item, index) {
                return h("a", { href: url(item[0]), "aria-current": isCurrent(item[0]) ? "page" : null },
                    h("span", { class: "num", text: "0" + (index + 1) }),
                    h("span", {}, h("strong", { text: item[1] }), h("small", { text: item[2] })),
                    icon("out"));
            })),
            foot);
        currentUser().then(function (user) {
            append(foot, h("div", { class: "v-drawer-actions" }, user ? [
                h("a", { class: "v-btn v-btn-primary v-btn-sm", href: url(accountLinks(user)[0][0]), text: accountLinks(user)[0][1] }),
                h("button", { type: "button", class: "v-btn v-btn-outline v-btn-sm", text: "Đăng xuất", onclick: logout })
            ] : [
                h("a", { class: "v-btn v-btn-primary v-btn-sm", href: url("pages/login.html"), text: "Đăng nhập" }),
                h("a", { class: "v-btn v-btn-outline v-btn-sm", href: url("pages/register.html"), text: "Đăng ký" })
            ]));
            append(foot, h("div", { class: "v-drawer-meta" }, h("span", { text: "Tiếng Việt" }),
                h("a", { class: "v-link", href: url("pages/contact.html"), text: "Trung tâm trợ giúp ↗" })));
        });
        showOverlay(drawer);
        drawer.querySelector(".v-close").focus();
    }

    function searchForm(options) {
        options = options || {};
        var input = h("input", { type: "search", name: "q", placeholder: "Vị trí, kỹ năng hoặc công ty", "aria-label": "Từ khóa", value: options.q || "", autocomplete: "off" });
        var select = h("select", { name: "province_id", "aria-label": "Địa điểm" }, h("option", { value: "", text: "Tất cả địa điểm" }));
        categories().then(function (data) {
            fillSelect(select, data.provinces, "Tất cả địa điểm");
            if (options.province_id) select.value = String(options.province_id);
        });
        var form = h("form", { class: "v-searchbar " + (options.variant || ""), role: "search", action: url("pages/jobs.html"), method: "get" },
            h("label", {}, h("img", { src: url("src/assets/images/icons/search-lg.svg"), alt: "", width: 24, height: 24 }), input),
            h("span", { class: "divider" }),
            h("label", {}, h("img", { src: url("src/assets/images/icons/pin.svg"), alt: "", width: 23, height: 23 }), select),
            h("button", { type: "submit", class: "v-btn v-btn-primary" }, "Tìm việc ngay", icon("arrow")));
        form.addEventListener("submit", function (event) {
            if (options.onSubmit) { event.preventDefault(); options.onSubmit({ q: input.value.trim(), province_id: select.value }); }
            else if (!select.value) select.disabled = true; // không gửi tham số rỗng lên URL
        });
        form.input = input;
        return form;
    }

    function openSearch() {
        var suggest = h("div", { class: "v-suggest" });
        var form = searchForm({ variant: "v-searchbar-outline" });
        var popular = ["Product Designer", "Marketing", "Công nghệ thông tin", "Business Analyst", "Phân tích dữ liệu", "Kế toán", "Thực tập sinh"];
        var timer = null;
        function loadSuggestions() {
            api("/jobs", { auth: false, query: { q: form.input.value.trim(), page_size: 3 } }).then(function (data) {
                clear(suggest);
                if (!data.items.length) return suggest.appendChild(h("p", { class: "v-muted", text: "Chưa có việc làm phù hợp với từ khóa này." }));
                data.items.forEach(function (job) {
                    suggest.appendChild(h("a", { href: jobUrl(job.id) }, icon("search"),
                        h("span", {}, h("strong", { text: job.title }),
                            h("small", { text: [job.company_name, job.province_name, salary(job)].filter(Boolean).join("  ·  ") })),
                        h("span", { class: "v-link", text: "Xem việc làm ↗" })));
                });
            }).catch(function () { clear(suggest); });
        }
        form.input.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(loadSuggestions, 300); });
        var panel = h("div", { class: "v-search-panel", role: "dialog", "aria-modal": "true", "aria-label": "Tìm kiếm việc làm" },
            h("div", { class: "v-wrap" },
                h("div", { class: "v-search-top" }, h("p", { class: "v-eyebrow", text: "Tìm kiếm việc làm" }),
                    h("button", { type: "button", class: "v-close", onclick: closeOverlay }, "Đóng", icon("close", "v-icon-lg"))),
                form,
                h("div", { class: "v-search-cols" },
                    h("div", {}, h("p", { class: "v-eyebrow", text: "Tìm kiếm phổ biến" }),
                        h("div", { class: "v-chips" }, popular.map(function (word) {
                            return h("a", { class: "v-chip v-chip-lg", href: url("pages/jobs.html") + "?q=" + encodeURIComponent(word), text: word });
                        }))),
                    h("div", {}, h("p", { class: "v-eyebrow", text: "Gợi ý cho bạn" }), suggest))));
        showOverlay(panel);
        form.input.focus();
        loadSuggestions();
    }

    function renderFooter(mount) {
        function col(title, links) {
            return h("div", {}, h("h2", { text: title }), h("ul", {}, links.map(function (l) { return h("li", {}, h("a", { href: url(l[0]), text: l[1] })); })));
        }
        clear(mount).appendChild(h("footer", { class: "v-footer" },
            h("div", { class: "v-wrap" },
                h("div", { class: "v-footer-brand", text: "VIECO" }),
                h("div", { class: "v-footer-cols" },
                    h("div", {}, h("h2", { text: "Về Vieco" }),
                        h("p", { text: "Nền tảng kết nối ứng viên với doanh nghiệp. Cùng bạn tìm kiếm cơ hội, phát triển sự nghiệp và kiến tạo những kết nối có ý nghĩa." })),
                    col("Dành cho bạn", [["pages/jobs.html", "Khám phá việc làm"], ["pages/cv-library.html", "Tạo CV chuyên nghiệp"], ["pages/profile.html", "Hồ sơ tìm việc"], ["pages/for-employers.html", "Dành cho nhà tuyển dụng"]]),
                    col("Hỗ trợ & liên hệ", [["pages/contact.html", "Trung tâm trợ giúp"], ["pages/contact.html#faq", "Hướng dẫn ứng tuyển"], ["pages/contact.html", "Kết nối với Vieco ↗"], ["pages/contact.html", "Báo cáo tin tuyển dụng"]]),
                    col("Thông tin pháp lý", [["pages/contact.html#faq", "Điều khoản sử dụng"], ["pages/contact.html#faq", "Chính sách bảo mật"], ["pages/contact.html#faq", "Quy chế hoạt động"]])),
                h("div", { class: "v-footer-bottom" }, h("span", { text: "© 2026 Vieco. Chạm cơ hội, mở tương lai." }), h("span", { text: "Tiếng Việt" })))));
    }

    function mount() {
        var header = document.getElementById("v-header"), footer = document.getElementById("v-footer");
        if (header) renderHeader(header);
        if (footer) renderFooter(footer);
    }

    window.Vieco = {
        url: url, h: h, clear: clear, icon: icon, api: api, download: download, goLogin: goLogin, currentUser: currentUser, requireRole: requireRole,
        categories: categories, fillSelect: fillSelect, salary: salary, date: date, ago: ago, initials: initials, shortName: shortName,
        brand: brand, brandColor: brandColor, logo: logo, media: media, coverImage: coverImage, linkInfo: linkInfo, externalLink: externalLink, prose: prose, lines: lines, roleLabel: roleLabel,
        badge: badge, toast: toast, note: note, loading: loading, empty: empty, saveButton: saveButton, jobCard: jobCard, jobRow: jobRow, companyCard: companyCard,
        jobUrl: jobUrl, companyUrl: companyUrl, pagination: pagination, modal: modal, confirm: confirmDialog, searchForm: searchForm,
        openSearch: openSearch, logout: logout, refreshUnread: function () { refreshUnread(); },
        EXPERIENCE: EXPERIENCE, EMPLOYMENT: EMPLOYMENT, APP_STATUS: APP_STATUS, JOB_STATUS: JOB_STATUS, COMPANY_STATUS: COMPANY_STATUS
    };

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
    else mount();
}());
