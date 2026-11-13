(function () {
    "use strict";
    const Auth = window.ViecoAuthApi;
    const Api = window.ViecoEmployerApi;
    const client = Api.createClient();
    const $ = function (id) { return document.getElementById(id); };
    const companyForm = $("company-form"), jobForm = $("job-form");
    const state = { company: null, companyBusy: false, jobBusy: false, ready: false, jobLoaded: false,
        companyDirty: false, jobDirty: false, job: null, jobId: new URLSearchParams(location.search).get("job_id") };
    const labels = { DRAFT: "Nháp", PENDING: "Chờ duyệt", APPROVED: "Đã duyệt", REJECTED: "Bị từ chối",
        CLOSED: "Đã đóng", EXPIRED: "Hết hạn" };

    function notice(id, message, variant) {
        const el = $(id);
        el.textContent = message || "";
        el.className = "notice" + (variant ? " " + variant : "");
        el.hidden = !message;
    }

    function status(id, record, empty) {
        const el = $(id);
        el.textContent = record ? (labels[record.status] || record.status) : empty;
        el.dataset.status = record ? record.status : "";
    }

    function loginUrl() {
        return "login.html?redirect=" + encodeURIComponent("employer.html" + location.search + location.hash);
    }

    function errorMessage(id, error, form) {
        notice(id, error.message || "Không thể xử lý yêu cầu. Vui lòng thử lại.", "error");
        if (form) showErrors(form, error.fieldErrors || {});
        if (error.status === 401) {
            Auth.clearAuthSession();
            $("page-recovery").hidden = false;
            $("retry-load").hidden = true;
            $("login-link").hidden = false;
            $("login-link").href = loginUrl();
            notice("page-message", "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để tiếp tục.", "warning");
        }
    }

    function clearErrors(form) {
        form.querySelectorAll("[aria-invalid]").forEach(function (el) { el.removeAttribute("aria-invalid"); });
        form.querySelectorAll(".field-error").forEach(function (el) { el.textContent = ""; });
    }

    function showErrors(form, errors) {
        let first = null;
        Object.keys(errors).forEach(function (key) {
            const input = form.elements.namedItem(key);
            if (!input) return;
            input.setAttribute("aria-invalid", "true");
            input.closest(".field").querySelector(".field-error").textContent = errors[key];
            if (!first) first = input;
        });
        if (first) first.focus();
    }

    function values(form, fields) {
        const data = {};
        fields.forEach(function (key) { data[key] = form.elements.namedItem(key).value; });
        return data;
    }

    function fill(form, fields, record) {
        fields.forEach(function (key) {
            const input = form.elements.namedItem(key);
            const value = record[key] == null ? "" : String(record[key]);
            // Existing records may reference an inactive catalog entry; preserve its ID.
            if (input.tagName === "SELECT" && value && !Array.from(input.options).some(function (o) { return o.value === value; })) {
                input.add(new Option("Mục cũ không còn sử dụng (#" + value + ")", value));
            }
            input.value = value;
        });
    }

    function renderCompany() {
        const company = state.company;
        status("company-status", company, "Chưa tạo hồ sơ");
        notice("company-rejection", company && company.status === "REJECTED" ? "Lý do từ chối: " + (company.reject_reason || "Chưa có lý do.") : "", "warning");
        $("save-company").textContent = state.companyBusy ? "Đang lưu…" : (company ? "Lưu thay đổi" : "Tạo hồ sơ và gửi duyệt");
        $("resubmit-company").hidden = !company || company.status !== "REJECTED";
        const owner = !company || company.member_role === "OWNER";
        $("company-permission").hidden = owner;
        $("company-fields").disabled = !state.ready || !owner || state.companyBusy;
        companyForm.setAttribute("aria-busy", String(state.companyBusy));
        $("refresh-company").disabled = state.companyBusy || !state.ready;
        renderJobGate();
    }

    function renderJobGate() {
        const approved = state.company && state.company.status === "APPROVED";
        let gate = "";
        if (!state.company) gate = "Hãy tạo hồ sơ công ty và chờ được duyệt trước khi tạo tin tuyển dụng.";
        else if (!approved) gate = "Công ty đang ở trạng thái “" + labels[state.company.status] + "”. Bạn có thể đăng tin sau khi công ty được duyệt.";
        else if (state.job && !["DRAFT", "REJECTED"].includes(state.job.status)) {
            gate = "Tin đang ở trạng thái “" + (labels[state.job.status] || state.job.status) + "”. Hiện chỉ có thể chỉnh sửa tin nháp hoặc bị từ chối.";
        }
        notice("job-gate", gate, "warning");
        $("job-fields").disabled = !state.ready || !approved || state.jobBusy || !state.jobLoaded || Boolean(gate);
        jobForm.setAttribute("aria-busy", String(state.jobBusy));
        $("save-draft").textContent = state.jobBusy ? "Đang lưu…" : "Lưu nháp";
        $("submit-job").textContent = state.jobBusy ? "Đang xử lý…" : "Gửi duyệt";
    }

    function selectPanel() {
        const job = location.hash === "#job";
        $("company-panel").hidden = job;
        $("job-panel").hidden = !job;
        $("company-tab").toggleAttribute("aria-current", !job);
        $("job-tab").toggleAttribute("aria-current", job);
        (job ? $("job-tab") : $("company-tab")).setAttribute("aria-current", "page");
        if (job && state.ready && !state.jobLoaded && !state.jobBusy) loadJob();
    }

    async function loadCompany() {
        try { state.company = await client.company(); }
        catch (error) {
            if (error.status !== 404) throw error;
            state.company = null;
        }
        if (state.company) fill(companyForm, Api.COMPANY_FIELDS, state.company);
        state.companyDirty = false;
        renderCompany();
    }

    async function loadJob() {
        if (!state.jobId) {
            state.jobLoaded = true;
            renderJobGate();
            return;
        }
        if (!/^[1-9]\d*$/.test(state.jobId)) {
            notice("job-message", "Mã tin tuyển dụng không hợp lệ. Hãy mở lại liên kết của tin cần sửa.", "error");
            return;
        }
        state.jobBusy = true;
        $("retry-job").hidden = true;
        renderJobGate();
        notice("job-message", "Đang tải nội dung tin…");
        try {
            const job = await client.job(state.jobId);
            if (String(job.id) !== state.jobId || !state.company || job.company_id !== state.company.id) {
                throw new Error("Tin không thuộc công ty của bạn hoặc dữ liệu trả về không hợp lệ.");
            }
            if (job.salary_currency && job.salary_currency !== "VND") {
                throw new Error("Biểu mẫu hiện hỗ trợ lương VND. Tin này dùng đơn vị tiền khác nên chưa thể chỉnh sửa tại đây.");
            }
            state.job = job;
            state.jobLoaded = true;
            fill(jobForm, Api.JOB_FIELDS, job);
            state.jobDirty = false;
            $("job-heading").textContent = "Chỉnh sửa tin tuyển dụng";
            status("job-status", job, "Chưa lưu");
            notice("job-rejection", job.status === "REJECTED" ? "Lý do từ chối: " + (job.reject_reason || "Chưa có lý do.") : "", "warning");
            notice("job-message", "");
        } catch (error) { errorMessage("job-message", error); $("retry-job").hidden = false; }
        finally { state.jobBusy = false; renderJobGate(); }
    }

    async function saveCompany(resubmit) {
        if (state.companyBusy || $("company-fields").disabled) return;
        clearErrors(companyForm);
        const result = Api.validateCompany(values(companyForm, Api.COMPANY_FIELDS));
        if (!result.valid) {
            notice("company-message", "Vui lòng kiểm tra các trường được đánh dấu.", "error");
            showErrors(companyForm, result.errors);
            return;
        }
        state.companyBusy = true;
        renderCompany();
        notice("company-message", "Đang lưu hồ sơ…");
        let saved = false;
        try {
            state.company = await client.saveCompany(Boolean(state.company), result.payload);
            state.companyDirty = false;
            saved = true;
            if (resubmit) state.company = await client.resubmitCompany();
            notice("company-message", resubmit || state.company.status === "PENDING" ? "Đã lưu hồ sơ. Công ty đang chờ Admin xét duyệt." : "Đã lưu thay đổi hồ sơ công ty.", "success");
        } catch (error) {
            if (saved) error.message = "Hồ sơ đã được lưu nhưng chưa gửi duyệt lại. " + error.message;
            errorMessage("company-message", error, companyForm);
        } finally {
            state.companyBusy = false;
            renderCompany();
            const invalid = companyForm.querySelector('[aria-invalid="true"]');
            if (invalid) invalid.focus();
        }
    }

    async function saveJob(submit) {
        if (state.jobBusy || $("job-fields").disabled) return;
        clearErrors(jobForm);
        const result = Api.validateJob(values(jobForm, Api.JOB_FIELDS), submit);
        if (!result.valid) {
            notice("job-message", "Vui lòng kiểm tra các trường được đánh dấu.", "error");
            showErrors(jobForm, result.errors);
            return;
        }
        state.jobBusy = true;
        renderJobGate();
        notice("job-message", submit ? "Đang lưu tin và gửi duyệt…" : "Đang lưu nháp…");
        let saved = false;
        try {
            const job = await client.saveJob(state.jobId, result.payload);
            if (!Number.isSafeInteger(job.id) || job.id < 1 || job.company_id !== state.company.id ||
                (state.jobId && String(job.id) !== state.jobId)) throw new Error("Dữ liệu tin trả về không hợp lệ. Vui lòng kiểm tra lại trước khi lưu tiếp.");
            state.job = job;
            state.jobId = String(job.id);
            state.jobDirty = false;
            saved = true;
            // Save the new ID before submitting: retrying a failed submit must not create a duplicate.
            const url = new URL(location.href);
            url.searchParams.set("job_id", state.jobId);
            history.replaceState(null, "", url.pathname + url.search + "#job");
            $("job-heading").textContent = "Chỉnh sửa tin tuyển dụng";
            if (submit) state.job = await client.submitJob(state.jobId);
            status("job-status", state.job, "Chưa lưu");
            notice("job-rejection", state.job.status === "REJECTED" ? "Lý do từ chối: " + (state.job.reject_reason || "Chưa có lý do.") : "", "warning");
            notice("job-message", submit ? "Đã gửi tin đến Admin xét duyệt." : "Đã lưu nháp. Bạn có thể tiếp tục chỉnh sửa hoặc quay lại bằng liên kết trang này.", "success");
        } catch (error) {
            if (saved) error.message = "Đã lưu nội dung tin nhưng chưa gửi duyệt. " + error.message;
            status("job-status", state.job, "Chưa lưu");
            errorMessage("job-message", error, jobForm);
        } finally {
            state.jobBusy = false;
            renderJobGate();
            const invalid = jobForm.querySelector('[aria-invalid="true"]');
            if (invalid) invalid.focus();
        }
    }

    async function boot() {
        $("page-recovery").hidden = true;
        notice("page-message", "Đang tải thông tin tài khoản và công ty…");
        const token = Auth.getAuthToken();
        if (!token) { location.replace(loginUrl()); return; }
        try {
            const user = await Auth.fetchCurrentUser(token);
            if (user.role !== "EMPLOYER") {
                notice("page-message", "Trang này dành cho tài khoản Nhà tuyển dụng. Bạn có thể quay về trang chủ hoặc đăng xuất để đổi tài khoản.", "warning");
                $("logout").hidden = false;
                return;
            }
            $("account-name").textContent = user.full_name;
            $("logout").hidden = false;
            const catalog = await client.categories();
            if (!Array.isArray(catalog.industries) || !catalog.industries.length || !Array.isArray(catalog.provinces) || !catalog.provinces.length) {
                throw new Error("Danh mục ngành nghề hoặc tỉnh/thành chưa sẵn sàng. Vui lòng thử lại sau.");
            }
            document.querySelectorAll("[data-catalog]").forEach(function (select) {
                while (select.options.length > 1) select.remove(1);
                catalog[select.dataset.catalog].forEach(function (item) { select.add(new Option(item.name, String(item.id))); });
            });
            await loadCompany();
            state.ready = true;
            $("workspace").hidden = false;
            notice("page-message", "");
            renderCompany();
            selectPanel();
        } catch (error) {
            errorMessage("page-message", error);
            $("page-recovery").hidden = false;
            $("retry-load").hidden = error.status === 401;
        }
    }

    [companyForm, jobForm].forEach(function (form) {
        form.querySelectorAll(".field").forEach(function (field) {
            const input = field.querySelector("input, select, textarea");
            input.setAttribute("aria-describedby", field.querySelector(".field-error").id);
        });
        form.addEventListener("input", function (event) {
            state[form === companyForm ? "companyDirty" : "jobDirty"] = true;
            event.target.removeAttribute("aria-invalid");
            const field = event.target.closest(".field");
            if (field) field.querySelector(".field-error").textContent = "";
        });
    });
    companyForm.addEventListener("submit", function (event) { event.preventDefault(); saveCompany(false); });
    $("resubmit-company").addEventListener("click", function () { saveCompany(true); });
    jobForm.addEventListener("submit", function (event) { event.preventDefault(); saveJob(Boolean(event.submitter && event.submitter.value === "submit")); });
    $("refresh-company").addEventListener("click", async function () {
        if (state.companyDirty && !confirm("Tải lại hồ sơ sẽ thay thế các thay đổi chưa lưu. Tiếp tục?")) return;
        state.companyBusy = true;
        renderCompany();
        try { await loadCompany(); notice("company-message", "Đã cập nhật trạng thái công ty.", "success"); }
        catch (error) { errorMessage("company-message", error); }
        finally { state.companyBusy = false; renderCompany(); }
    });
    $("retry-load").addEventListener("click", boot);
    $("retry-job").addEventListener("click", loadJob);
    $("logout").addEventListener("click", async function () {
        if ((state.companyDirty || state.jobDirty) && !confirm("Bạn có thay đổi chưa lưu. Vẫn đăng xuất?")) return;
        if (state.companyBusy || state.jobBusy) return;
        $("logout").disabled = true;
        try {
            await Auth.logoutUser(Auth.getAuthToken());
            Auth.clearAuthSession();
            state.companyDirty = state.jobDirty = false;
            location.href = "login.html";
        } catch (error) {
            if (error.status === 401) {
                Auth.clearAuthSession();
                state.companyDirty = state.jobDirty = false;
                location.href = "login.html";
            } else errorMessage("page-message", error);
        } finally { $("logout").disabled = false; }
    });
    window.addEventListener("hashchange", selectPanel);
    window.addEventListener("beforeunload", function (event) {
        if (state.companyDirty || state.jobDirty || state.companyBusy || state.jobBusy) {
            event.preventDefault(); event.returnValue = "";
        }
    });
    $("job-deadline").min = Api.localDate();
    boot();
}());
