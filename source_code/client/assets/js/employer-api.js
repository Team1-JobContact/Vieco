(function (root, factory) {
    if (typeof module === "object" && module.exports) module.exports = factory();
    else root.ViecoEmployerApi = factory(root.ViecoAuthApi);
}(typeof globalThis !== "undefined" ? globalThis : this, function (auth) {
    "use strict";

    const COMPANY_FIELDS = ["name", "industry_id", "size", "website", "address", "province_id", "description"];
    const JOB_FIELDS = ["title", "industry_id", "province_id", "work_address", "description", "requirements",
        "benefits", "salary_min", "salary_max", "experience_level", "employment_type", "positions", "deadline"];
    const SIZES = ["1-50", "51-200", "201-500", "501-1000", "1000+"];
    const EMPLOYMENT_TYPES = ["FULL_TIME", "PART_TIME", "INTERNSHIP", "CONTRACT", "FREELANCE"];
    const EXPERIENCE_LEVELS = ["NONE", "UNDER_1", "FROM_1_TO_3", "FROM_3_TO_5", "OVER_5"];

    function text(value) { return typeof value === "string" ? value.trim() : ""; }

    function localDate(now) {
        // Business dates are based on the project's Asia/Saigon timezone, not UTC/browser timezone.
        return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh", year: "numeric",
            month: "2-digit", day: "2-digit" }).format(now || new Date());
    }

    function isDate(value) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
        const date = new Date(value + "T00:00:00Z");
        return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
    }

    function validate(fields, kind, submit, today) {
        const payload = {}, errors = {};
        (kind === "company" ? COMPANY_FIELDS : JOB_FIELDS).forEach(function (key) {
            const value = text(String(fields[key] == null ? "" : fields[key]));
            payload[key] = value || null;
        });
        function required(key, label) {
            if (payload[key] === null) errors[key] = "Vui lòng nhập " + label + ".";
        }
        function length(key, max, min) {
            if (payload[key] !== null && (payload[key].length > max || payload[key].length < (min || 0))) {
                errors[key] = "Độ dài phải " + (min ? "từ " + min + " đến " : "không quá ") + max + " ký tự.";
            }
        }
        function integer(key, min) {
            if (payload[key] === null) return;
            const raw = payload[key];
            const n = Number(raw);
            if (!/^\d+$/.test(raw) || !Number.isSafeInteger(n) || n < min) {
                errors[key] = "Vui lòng nhập số nguyên " + (min === 0 ? "không âm" : "lớn hơn 0") + ".";
            } else payload[key] = n;
        }
        integer("industry_id", 1);
        integer("province_id", 1);
        if (kind === "company") {
            required("name", "tên công ty"); required("industry_id", "ngành nghề");
            required("size", "quy mô"); required("address", "địa chỉ"); required("province_id", "tỉnh/thành");
            length("name", 200, 2); length("address", 255); length("description", 10000); length("website", 255);
            if (payload.size && !SIZES.includes(payload.size)) errors.size = "Vui lòng chọn quy mô hợp lệ.";
            if (payload.website && !/^https?:\/\/[^\s/$.?#][^\s]*$/i.test(payload.website)) {
                errors.website = "Website phải bắt đầu bằng http:// hoặc https:// và không có khoảng trắng.";
            }
        } else {
            required("title", "tiêu đề tin"); length("title", 200);
            length("work_address", 255);
            ["description", "requirements", "benefits"].forEach(function (key) { length(key, 10000); });
            integer("salary_min", 0); integer("salary_max", 0); integer("positions", 1);
            if (payload.positions === null) payload.positions = 1;
            if (payload.salary_min !== null && payload.salary_max !== null && payload.salary_min > payload.salary_max) {
                errors.salary_max = "Lương tối đa phải lớn hơn hoặc bằng lương tối thiểu.";
            }
            if (payload.employment_type && !EMPLOYMENT_TYPES.includes(payload.employment_type)) {
                errors.employment_type = "Vui lòng chọn hình thức làm việc hợp lệ.";
            }
            if (payload.experience_level && !EXPERIENCE_LEVELS.includes(payload.experience_level)) {
                errors.experience_level = "Vui lòng chọn kinh nghiệm hợp lệ.";
            }
            if (submit) {
                required("description", "mô tả công việc"); required("requirements", "yêu cầu ứng viên");
                required("province_id", "tỉnh/thành"); required("work_address", "địa điểm làm việc");
                required("employment_type", "hình thức làm việc"); required("deadline", "hạn nộp hồ sơ");
            }
            if (payload.deadline && (!isDate(payload.deadline) || payload.deadline < (today || localDate()))) {
                errors.deadline = "Hạn nộp phải là ngày hợp lệ từ hôm nay trở đi.";
            }
            payload.salary_currency = "VND";
        }
        return { valid: Object.keys(errors).length === 0, errors: errors, payload: payload };
    }

    function parseError(status, data) {
        const error = new Error("Không thể xử lý yêu cầu. Vui lòng thử lại.");
        error.status = status;
        error.fieldErrors = {};
        const detail = data && data.detail;
        if (Array.isArray(detail)) {
            detail.forEach(function (item) {
                const key = (item.loc || []).slice(-1)[0];
                if (typeof key === "string") error.fieldErrors[key] = String(item.msg || "Dữ liệu không hợp lệ").replace(/^Value error,\s*/i, "");
            });
            error.message = "Vui lòng kiểm tra các trường được đánh dấu.";
        } else if (typeof detail === "string") error.message = detail;
        else if (status === 401) error.message = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
        else if (status === 403) error.message = "Bạn không có quyền thực hiện thao tác này.";
        else if (status === 404) error.message = "Không tìm thấy dữ liệu yêu cầu.";
        else if (status === 409) error.message = "Dữ liệu hoặc trạng thái đã thay đổi. Vui lòng kiểm tra lại.";
        else if (status >= 500) error.message = "Máy chủ đang gặp sự cố. Vui lòng thử lại sau.";
        return error;
    }

    function createClient(options) {
        const opts = options || {};
        async function request(path, method, body) {
            const base = opts.baseUrl || auth.getApiBaseUrl();
            const token = opts.token || auth.getAuthToken();
            const controller = new AbortController();
            const timer = setTimeout(function () { controller.abort(); }, 15000);
            try {
                const response = await (opts.fetch || fetch)(base.replace(/\/+$/, "") + path, {
                    method: method || "GET", signal: controller.signal,
                    headers: Object.assign({ Accept: "application/json" }, token ? { Authorization: "Bearer " + token } : {},
                        body !== undefined ? { "Content-Type": "application/json" } : {}),
                    body: body !== undefined ? JSON.stringify(body) : undefined,
                });
                let data = null;
                if (response.status !== 204) {
                    try { data = await response.json(); } catch (_) { /* Handled below. */ }
                }
                if (!response.ok) throw parseError(response.status, data);
                if (response.status !== 204 && data === null) throw new Error("Máy chủ trả về dữ liệu không hợp lệ.");
                return data;
            } catch (error) {
                if (error.status) throw error;
                const network = new Error(error.name === "AbortError" ? "Yêu cầu quá thời gian. Vui lòng thử lại." :
                    (error.message === "Máy chủ trả về dữ liệu không hợp lệ." ? error.message : "Không thể kết nối máy chủ. Dữ liệu bạn nhập vẫn được giữ trên trang."));
                network.fieldErrors = {};
                throw network;
            } finally { clearTimeout(timer); }
        }
        function jobRequest(path, method, body) {
            return request(path, method, body).catch(function (error) {
                if (error.status === 404 || error.status === 405 || error.status === 501) {
                    error.message = "Chưa thể tải hoặc lưu tin này. Vui lòng thử lại sau hoặc liên hệ người quản lý hệ thống.";
                }
                throw error;
            });
        }
        return {
            categories: function () { return request("/categories"); },
            company: function () { return request("/employer/company"); },
            saveCompany: function (exists, body) { return request("/employer/company", exists ? "PATCH" : "POST", body); },
            resubmitCompany: function () { return request("/employer/company/resubmit", "POST"); },
            // PB-014 integration contract is documented in docs/PB-015.md.
            job: function (id) { return jobRequest("/employer/jobs/" + encodeURIComponent(id)); },
            saveJob: function (id, body) { return jobRequest(id ? "/jobs/" + encodeURIComponent(id) : "/jobs", id ? "PATCH" : "POST", body); },
            submitJob: function (id) { return jobRequest("/jobs/" + encodeURIComponent(id) + "/submit", "POST"); },
        };
    }

    return { COMPANY_FIELDS: COMPANY_FIELDS, JOB_FIELDS: JOB_FIELDS, localDate: localDate,
        validateCompany: function (fields) { return validate(fields, "company"); },
        validateJob: function (fields, submit, today) { return validate(fields, "job", submit, today); },
        parseError: parseError, createClient: createClient };
}));
