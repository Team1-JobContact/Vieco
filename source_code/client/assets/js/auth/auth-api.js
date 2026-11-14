(function (root, factory) {
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.ViecoAuthApi = factory();
    }
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";
    const TOKEN_KEY = "vieco_access_token";
    const USER_KEY = "vieco_user";
    const REQUEST_TIMEOUT_MS = 15000;

    function getApiBaseUrl() {
        if (typeof window !== "undefined") {
            if (window.VIECO_API_BASE_URL) {
                return String(window.VIECO_API_BASE_URL).replace(/\/+$/, "");
            }
            try {
                const stored = window.localStorage.getItem("vieco_api_base_url");
                if (stored) {
                    return stored.replace(/\/+$/, "");
                }
            } catch (_) {
                // Ignore storage restrictions
            }
        }
        return DEFAULT_API_BASE_URL;
    }

    function utf8ByteLength(str) {
        if (typeof TextEncoder !== "undefined") {
            return new TextEncoder().encode(str).length;
        }
        return unescape(encodeURIComponent(str)).length;
    }

    function validateEmail(email) {
        const value = typeof email === "string" ? email.trim() : "";
        if (!value) {
            return { valid: false, message: "Vui lòng nhập email" };
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)) {
            return { valid: false, message: "Email không đúng định dạng (ví dụ: ten@domain.com)" };
        }
        return { valid: true, value: value, message: "" };
    }

    function inspectPassword(password) {
        const value = typeof password === "string" ? password : "";
        return {
            minLength: value.length >= 8,
            maxBytes: value.length > 0 && utf8ByteLength(value) <= 72,
            hasLetter: /[A-Za-z]/.test(value),
            hasDigit: /\d/.test(value),
        };
    }

    function validatePassword(password, options) {
        const opts = options || {};
        const value = typeof password === "string" ? password : "";
        if (!value) {
            return {
                valid: false,
                message: "Vui lòng nhập mật khẩu",
                rules: inspectPassword(value),
            };
        }
        const rules = inspectPassword(value);
        if (opts.loginOnly) {
            return { valid: true, message: "", rules: rules };
        }
        if (!rules.minLength) {
            return { valid: false, message: "Mật khẩu phải có ít nhất 8 ký tự", rules: rules };
        }
        if (!rules.maxBytes) {
            return { valid: false, message: "Mật khẩu tối đa 72 byte", rules: rules };
        }
        if (!rules.hasLetter || !rules.hasDigit) {
            return { valid: false, message: "Mật khẩu phải gồm cả chữ cái và chữ số", rules: rules };
        }
        return { valid: true, message: "", rules: rules };
    }

    function validateFullName(fullName) {
        const value = typeof fullName === "string" ? fullName.trim() : "";
        if (!value) {
            return { valid: false, message: "Vui lòng nhập họ và tên" };
        }
        if (value.length < 2 || value.length > 150) {
            return { valid: false, message: "Họ tên phải từ 2 đến 150 ký tự" };
        }
        return { valid: true, value: value, message: "" };
    }

    function validatePhone(phone) {
        const value = typeof phone === "string" ? phone.trim() : "";
        if (!value) {
            return { valid: true, value: null, message: "" };
        }
        if (!/^\+?\d{9,15}$/.test(value)) {
            return { valid: false, message: "Số điện thoại phải gồm 9–15 chữ số (có thể bắt đầu bằng +)" };
        }
        return { valid: true, value: value, message: "" };
    }

    function validateLoginForm(fields) {
        const errors = {};
        const emailRes = validateEmail(fields.email);
        if (!emailRes.valid) errors.email = emailRes.message;

        const passRes = validatePassword(fields.password, { loginOnly: true });
        if (!passRes.valid) errors.password = passRes.message;

        return {
            valid: Object.keys(errors).length === 0,
            errors: errors,
            payload: {
                email: emailRes.value || "",
                password: fields.password || "",
            },
        };
    }

    function validateRegisterForm(fields) {
        const errors = {};
        const role = fields.role === "EMPLOYER" ? "EMPLOYER" : "CANDIDATE";

        const nameRes = validateFullName(fields.full_name);
        if (!nameRes.valid) errors.full_name = nameRes.message;

        const emailRes = validateEmail(fields.email);
        if (!emailRes.valid) errors.email = emailRes.message;

        const phoneRes = validatePhone(fields.phone);
        if (!phoneRes.valid) errors.phone = phoneRes.message;

        const passRes = validatePassword(fields.password);
        if (!passRes.valid) errors.password = passRes.message;

        if (!fields.confirm_password) {
            errors.confirm_password = "Vui lòng xác nhận mật khẩu";
        } else if (fields.password !== fields.confirm_password) {
            errors.confirm_password = "Mật khẩu xác nhận không khớp";
        }

        if (!fields.accept_terms) {
            errors.accept_terms = "Bạn cần đồng ý với điều khoản sử dụng để tiếp tục";
        }

        return {
            valid: Object.keys(errors).length === 0,
            errors: errors,
            payload: {
                role: role,
                full_name: nameRes.value || "",
                email: emailRes.value || "",
                phone: phoneRes.value,
                password: fields.password || "",
            },
        };
    }

    function cleanValidationMessage(rawMsg, fieldName) {
        if (!rawMsg) return "Dữ liệu không hợp lệ";
        const msg = String(rawMsg).replace(/^Value error,\s*/i, "").trim();
        if (fieldName === "email" && /email address/i.test(msg)) {
            return "Email không đúng định dạng";
        }
        return msg;
    }

    function parseApiError(status, payload) {
        const fieldErrors = {};
        let title = "Đã có lỗi xảy ra";
        let message = "Không thể xử lý yêu cầu. Vui lòng thử lại.";
        let variant = "error";

        const detail = payload && payload.detail;

        if (status === 422 && Array.isArray(detail)) {
            title = "Thông tin chưa hợp lệ";
            const summaryMessages = [];
            detail.forEach(function (item) {
                const loc = Array.isArray(item.loc) ? item.loc : [];
                const field = loc[loc.length - 1];
                const cleanMsg = cleanValidationMessage(item.msg, field);
                if (typeof field === "string" && field !== "body") {
                    fieldErrors[field] = cleanMsg;
                }
                summaryMessages.push(cleanMsg);
            });
            message = summaryMessages[0] || "Vui lòng kiểm tra lại các trường thông tin.";
            return { status: status, title: title, message: message, variant: variant, fieldErrors: fieldErrors };
        }

        if (typeof detail === "string" && detail.trim()) {
            message = detail.trim();
        }

        if (status === 401) {
            title = "Đăng nhập thất bại";
        } else if (status === 403) {
            title = "Tài khoản bị khóa";
            message = typeof detail === "string" && detail.trim()
                ? detail.trim() + ". Vui lòng liên hệ quản trị viên để được hỗ trợ."
                : "Tài khoản của bạn đã bị khóa.";
        } else if (status === 409) {
            title = "Email đã tồn tại";
            fieldErrors.email = message;
        } else if (status === 429) {
            title = "Tạm thời bị giới hạn";
            variant = "warning";
        } else if (status >= 500) {
            title = "Lỗi hệ thống";
            if (!detail) {
                message = "Máy chủ đang gặp sự cố. Vui lòng thử lại sau.";
            }
        }

        return { status: status, title: title, message: message, variant: variant, fieldErrors: fieldErrors };
    }

    async function requestJson(path, options) {
        const opts = options || {};
        const url = getApiBaseUrl() + path;
        const headers = Object.assign({ "Accept": "application/json" }, opts.headers || {});
        if (opts.body !== undefined) {
            headers["Content-Type"] = "application/json";
        }
        if (opts.token) {
            headers["Authorization"] = "Bearer " + opts.token;
        }

        const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
        const timer = controller
            ? setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS)
            : null;

        let response;
        try {
            response = await fetch(url, {
                method: opts.method || "GET",
                headers: headers,
                body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
                signal: controller ? controller.signal : undefined,
            });
        } catch (err) {
            if (timer) clearTimeout(timer);
            const isAbort = err && err.name === "AbortError";
            const networkError = new Error(
                isAbort
                    ? "Yêu cầu quá thời gian phản hồi. Vui lòng thử lại."
                    : "Không thể kết nối đến máy chủ API. Hãy kiểm tra backend đang chạy và thử lại."
            );
            networkError.isNetworkError = true;
            networkError.title = isAbort ? "Hết thời gian chờ" : "Lỗi kết nối máy chủ";
            networkError.variant = "error";
            networkError.fieldErrors = {};
            throw networkError;
        }

        if (timer) clearTimeout(timer);

        let data = null;
        const contentType = response.headers ? (response.headers.get("content-type") || "") : "";
        if (contentType.indexOf("application/json") !== -1) {
            try {
                data = await response.json();
            } catch (_) {
                data = null;
            }
        }

        if (!response.ok) {
            const parsed = parseApiError(response.status, data);
            const apiError = new Error(parsed.message);
            apiError.status = parsed.status;
            apiError.title = parsed.title;
            apiError.variant = parsed.variant;
            apiError.fieldErrors = parsed.fieldErrors;
            throw apiError;
        }

        return data;
    }

    function registerUser(payload) {
        return requestJson("/auth/register", { method: "POST", body: payload });
    }

    function loginUser(payload) {
        return requestJson("/auth/login", { method: "POST", body: payload });
    }

    function fetchCurrentUser(token) {
        return requestJson("/auth/me", { method: "GET", token: token });
    }

    function logoutUser(token) {
        return requestJson("/auth/logout", { method: "POST", token: token });
    }

    function saveAuthSession(token, user, rememberMe) {
        if (typeof window === "undefined") return;
        const primary = rememberMe ? window.localStorage : window.sessionStorage;
        const secondary = rememberMe ? window.sessionStorage : window.localStorage;
        try {
            secondary.removeItem(TOKEN_KEY);
            secondary.removeItem(USER_KEY);
            primary.setItem(TOKEN_KEY, token);
            primary.setItem(USER_KEY, JSON.stringify(user));
        } catch (_) {
            // Ignore storage errors in restricted environments
        }
    }

    function getAuthToken() {
        if (typeof window === "undefined") return null;
        try {
            return window.localStorage.getItem(TOKEN_KEY) || window.sessionStorage.getItem(TOKEN_KEY);
        } catch (_) {
            return null;
        }
    }

    function getStoredUser() {
        if (typeof window === "undefined") return null;
        try {
            const raw = window.localStorage.getItem(USER_KEY) || window.sessionStorage.getItem(USER_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (_) {
            return null;
        }
    }

    function clearAuthSession() {
        if (typeof window === "undefined") return;
        try {
            window.localStorage.removeItem(TOKEN_KEY);
            window.localStorage.removeItem(USER_KEY);
            window.sessionStorage.removeItem(TOKEN_KEY);
            window.sessionStorage.removeItem(USER_KEY);
        } catch (_) {
            // Ignore storage errors
        }
    }

    function getRoleLabel(role) {
        switch (role) {
            case "CANDIDATE":
                return "Ứng viên";
            case "EMPLOYER":
                return "Nhà tuyển dụng";
            case "ADMIN":
                return "Quản trị viên";
            default:
                return role || "Thành viên";
        }
    }

    return {
        getApiBaseUrl: getApiBaseUrl,
        validateEmail: validateEmail,
        inspectPassword: inspectPassword,
        validatePassword: validatePassword,
        validateFullName: validateFullName,
        validatePhone: validatePhone,
        validateLoginForm: validateLoginForm,
        validateRegisterForm: validateRegisterForm,
        parseApiError: parseApiError,
        registerUser: registerUser,
        loginUser: loginUser,
        fetchCurrentUser: fetchCurrentUser,
        logoutUser: logoutUser,
        saveAuthSession: saveAuthSession,
        getAuthToken: getAuthToken,
        getStoredUser: getStoredUser,
        clearAuthSession: clearAuthSession,
        getRoleLabel: getRoleLabel,
    };
}));

