(function () {
    "use strict";

    var Api = window.ViecoAuthApi;
    if (!Api) return;

    var EYE_OPEN_SVG = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
    var EYE_OFF_SVG = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';

    var currentMode = "register";
    var gxTimer = null;

    function initNavbarToggle() {
        var toggle = document.getElementById("nav-toggle");
        var menu = document.getElementById("nav-menu");
        if (!toggle || !menu) return;
        toggle.addEventListener("click", function () {
            var expanded = menu.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        });
    }

    function initPasswordToggles() {
        var buttons = document.querySelectorAll("[data-toggle-password]");
        buttons.forEach(function (btn) {
            var targetId = btn.getAttribute("data-toggle-password");
            var input = document.getElementById(targetId);
            if (!input) return;

            btn.innerHTML = EYE_OPEN_SVG;
            btn.addEventListener("click", function () {
                var isPassword = input.type === "password";
                input.type = isPassword ? "text" : "password";
                btn.innerHTML = isPassword ? EYE_OFF_SVG : EYE_OPEN_SVG;
                btn.setAttribute("aria-pressed", isPassword ? "true" : "false");
                btn.setAttribute("aria-label", isPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu");
            });
        });
    }

    function getAlertIconSvg(variant) {
        if (variant === "success") {
            return '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
        }
        if (variant === "warning") {
            return '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
        }
        return '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
    }

    function showAlert(bannerEl, options) {
        if (!bannerEl) return;
        var variant = options.variant || "error";
        bannerEl.className = "auth-alert auth-alert--" + variant;
        bannerEl.innerHTML = "";

        var iconSpan = document.createElement("span");
        iconSpan.className = "auth-alert-icon";
        iconSpan.setAttribute("aria-hidden", "true");
        iconSpan.innerHTML = getAlertIconSvg(variant);

        var content = document.createElement("div");
        content.className = "auth-alert-content";

        if (options.title) {
            var titleEl = document.createElement("div");
            titleEl.className = "auth-alert-title";
            titleEl.textContent = options.title;
            content.appendChild(titleEl);
        }

        var msgEl = document.createElement("div");
        msgEl.textContent = options.message || "";
        content.appendChild(msgEl);

        if (options.actionText && typeof options.onAction === "function") {
            var actionBtn = document.createElement("button");
            actionBtn.type = "button";
            actionBtn.className = "auth-alert-action";
            actionBtn.textContent = options.actionText;
            actionBtn.addEventListener("click", options.onAction);
            content.appendChild(actionBtn);
        }

        bannerEl.appendChild(iconSpan);
        bannerEl.appendChild(content);
        bannerEl.classList.remove("hidden");
    }

    function hideAlert(bannerEl) {
        if (!bannerEl) return;
        bannerEl.classList.add("hidden");
        bannerEl.innerHTML = "";
    }

    function setFieldError(form, fieldName, message) {
        var group = form.querySelector('[data-field-group="' + fieldName + '"]');
        var errorEl = form.querySelector('[data-field-error="' + fieldName + '"]');
        var input = form.querySelector('[name="' + fieldName + '"]');
        if (group) group.classList.add("has-error");
        if (errorEl) errorEl.textContent = message || "";
        if (input) input.setAttribute("aria-invalid", "true");
    }

    function clearFieldError(form, fieldName) {
        var group = form.querySelector('[data-field-group="' + fieldName + '"]');
        var errorEl = form.querySelector('[data-field-error="' + fieldName + '"]');
        var input = form.querySelector('[name="' + fieldName + '"]');
        if (group) group.classList.remove("has-error");
        if (errorEl) errorEl.textContent = "";
        if (input) input.removeAttribute("aria-invalid");
    }

    function clearAllFieldErrors(form) {
        form.querySelectorAll("[data-field-group]").forEach(function (g) {
            g.classList.remove("has-error");
        });
        form.querySelectorAll("[data-field-error]").forEach(function (e) {
            e.textContent = "";
        });
        form.querySelectorAll("[aria-invalid]").forEach(function (i) {
            i.removeAttribute("aria-invalid");
        });
    }

    function setButtonLoading(button, isLoading, loadingText, defaultText) {
        if (!button) return;
        button.disabled = isLoading;
        button.setAttribute("aria-busy", isLoading ? "true" : "false");
        if (isLoading) {
            button.innerHTML = '<span class="spinner" aria-hidden="true"></span><span>' + loadingText + "</span>";
        } else {
            button.textContent = defaultText;
        }
    }

    function setFormDisabled(form, disabled) {
        form.querySelectorAll("input, button, select, textarea").forEach(function (el) {
            if (el.type === "submit") return;
            el.disabled = disabled;
        });
    }

    function sanitizeRedirectTarget(rawTarget) {
        if (!rawTarget || typeof rawTarget !== "string") return "../index.html";
        var trimmed = rawTarget.trim();
        if (trimmed.indexOf("http://") === 0 || trimmed.indexOf("https://") === 0 || trimmed.indexOf("//") === 0) {
            return "../index.html";
        }
        return trimmed;
    }

    function applyMode(mode, animate) {
        var shell = document.getElementById("neumorphic-main");
        var switchCtn = document.getElementById("switch-cnt");
        var switchC1 = document.getElementById("switch-c1");
        var switchC2 = document.getElementById("switch-c2");
        var switchCircles = document.querySelectorAll(".switch__circle");
        var aContainer = document.getElementById("a-container");
        var bContainer = document.getElementById("b-container");
        var mobileLoginBtn = document.getElementById("mobile-tab-login");
        var mobileRegisterBtn = document.getElementById("mobile-tab-register");

        if (!shell || !switchCtn || !aContainer || !bContainer) return;

        currentMode = mode === "login" ? "login" : "register";
        shell.setAttribute("data-active-mode", currentMode);

        if (animate) {
            if (gxTimer) window.clearTimeout(gxTimer);
            switchCtn.classList.add("is-gx");
            gxTimer = window.setTimeout(function () {
                switchCtn.classList.remove("is-gx");
            }, 1250);
        }

        var isLogin = currentMode === "login";

        switchCtn.classList.toggle("is-txr", isLogin);
        switchCircles.forEach(function (c) {
            c.classList.toggle("is-txr", isLogin);
        });

        if (switchC1) switchC1.classList.toggle("is-hidden", isLogin);
        if (switchC2) switchC2.classList.toggle("is-hidden", !isLogin);

        aContainer.classList.toggle("is-txl", isLogin);
        bContainer.classList.toggle("is-txl", isLogin);
        bContainer.classList.toggle("is-z200", isLogin);

        aContainer.setAttribute("aria-hidden", isLogin ? "true" : "false");
        bContainer.setAttribute("aria-hidden", isLogin ? "false" : "true");

        if (mobileLoginBtn) {
            mobileLoginBtn.classList.toggle("is-active", isLogin);
            mobileLoginBtn.setAttribute("aria-selected", isLogin ? "true" : "false");
        }
        if (mobileRegisterBtn) {
            mobileRegisterBtn.classList.toggle("is-active", !isLogin);
            mobileRegisterBtn.setAttribute("aria-selected", !isLogin ? "true" : "false");
        }

        document.title = isLogin ? "Đăng nhập - Vieco" : "Đăng ký tài khoản - Vieco";
    }

    function updatePasswordRulesUI(password) {
        var rules = Api.inspectPassword(password);
        var map = {
            minLength: rules.minLength,
            hasLetter: rules.hasLetter,
            hasDigit: rules.hasDigit,
            maxBytes: password.length === 0 ? false : rules.maxBytes,
        };
        Object.keys(map).forEach(function (key) {
            var item = document.querySelector('[data-password-rule="' + key + '"]');
            if (item) item.classList.toggle("is-valid", Boolean(map[key]));
        });
    }

    async function checkExistingSession(loginAlertEl) {
        var overlay = document.getElementById("session-overlay");
        var checkingBox = document.getElementById("session-checking-box");
        var activeBox = document.getElementById("session-active-box");
        var token = Api.getAuthToken();

        if (!token || !overlay) return;

        overlay.classList.remove("hidden");
        if (checkingBox) checkingBox.classList.remove("hidden");
        if (activeBox) activeBox.classList.add("hidden");

        try {
            var user = await Api.fetchCurrentUser(token);
            if (checkingBox) checkingBox.classList.add("hidden");
            if (activeBox) {
                var nameEl = document.getElementById("session-user-name");
                var metaEl = document.getElementById("session-user-meta");
                var logoutBtn = document.getElementById("session-logout-btn");
                if (nameEl) nameEl.textContent = user.full_name;
                if (metaEl) metaEl.textContent = user.email + " • " + Api.getRoleLabel(user.role);
                activeBox.classList.remove("hidden");

                if (logoutBtn) {
                    logoutBtn.onclick = async function () {
                        setButtonLoading(logoutBtn, true, "Đang đăng xuất...", "Đăng xuất");
                        try {
                            await Api.logoutUser(token);
                        } catch (_) {
                            // Clear local session even if token already expired
                        } finally {
                            Api.clearAuthSession();
                            overlay.classList.add("hidden");
                            setButtonLoading(logoutBtn, false, "Đang đăng xuất...", "Đăng xuất");
                            applyMode("login", false);
                            showAlert(loginAlertEl, {
                                variant: "success",
                                title: "Đã đăng xuất",
                                message: "Bạn đã đăng xuất khỏi phiên làm việc trước.",
                            });
                        }
                    };
                }
            }
        } catch (err) {
            overlay.classList.add("hidden");
            if (err && err.status === 401) {
                Api.clearAuthSession();
                applyMode("login", false);
                showAlert(loginAlertEl, {
                    variant: "info",
                    title: "Phiên đăng nhập đã hết hạn",
                    message: "Vui lòng đăng nhập lại để tiếp tục sử dụng Vieco.",
                });
            } else if (err && err.isNetworkError) {
                showAlert(loginAlertEl, {
                    variant: "warning",
                    title: err.title,
                    message: "Chưa kiểm tra được phiên hiện tại vì không kết nối được máy chủ API.",
                });
            }
        }
    }

    function initAuthForms() {
        var shell = document.getElementById("neumorphic-main");
        var loginForm = document.getElementById("login-form");
        var registerForm = document.getElementById("register-form");
        if (!shell || !loginForm || !registerForm) return;

        var loginAlert = document.getElementById("login-alert");
        var registerAlert = document.getElementById("register-alert");
        var loginSubmitBtn = document.getElementById("login-submit-btn");
        var registerSubmitBtn = document.getElementById("register-submit-btn");
        var loginBtnText = loginSubmitBtn ? loginSubmitBtn.textContent.trim() : "ĐĂNG NHẬP";
        var registerBtnText = registerSubmitBtn ? registerSubmitBtn.textContent.trim() : "ĐĂNG KÝ";

        var params = new URLSearchParams(window.location.search);
        var modeParam = (params.get("mode") || "").toLowerCase();
        var initialAttr = shell.getAttribute("data-initial-mode") || "register";
        var startMode = modeParam === "login" || modeParam === "register" ? modeParam : initialAttr;

        applyMode(startMode, false);

        // Switch triggers (overlay buttons, mobile tabs, navbar links)
        document.querySelectorAll("[data-switch-mode]").forEach(function (trigger) {
            trigger.addEventListener("click", function (e) {
                var targetMode = trigger.getAttribute("data-switch-mode");
                if (targetMode !== "login" && targetMode !== "register") return;
                e.preventDefault();
                if (targetMode !== currentMode) {
                    applyMode(targetMode, true);
                }
            });
        });

        // Login prefill & post-registration banner
        var loginEmailInput = loginForm.querySelector('[name="email"]');
        var loginPasswordInput = loginForm.querySelector('[name="password"]');
        var rememberInput = loginForm.querySelector('[name="remember_me"]');
        var redirectTarget = sanitizeRedirectTarget(params.get("redirect"));

        var prefillEmail = params.get("email");
        if (prefillEmail && loginEmailInput) {
            loginEmailInput.value = prefillEmail;
        }
        if (params.get("registered") === "1") {
            showAlert(loginAlert, {
                variant: "success",
                title: "Đăng ký tài khoản thành công",
                message: "Bạn có thể đăng nhập bằng email và mật khẩu vừa tạo.",
            });
        }

        // Register role selector
        var roleInputs = registerForm.querySelectorAll('input[name="role"]');
        var roleParam = (params.get("role") || "").toUpperCase();
        function syncRolePills() {
            roleInputs.forEach(function (radio) {
                var pill = radio.closest(".neu-role-option");
                if (pill) pill.classList.toggle("is-selected", radio.checked);
            });
        }
        if (roleParam === "EMPLOYER" || roleParam === "CANDIDATE") {
            roleInputs.forEach(function (r) { r.checked = r.value === roleParam; });
        }
        syncRolePills();
        roleInputs.forEach(function (r) { r.addEventListener("change", syncRolePills); });

        var regNameInput = registerForm.querySelector('[name="full_name"]');
        var regPhoneInput = registerForm.querySelector('[name="phone"]');
        var regEmailInput = registerForm.querySelector('[name="email"]');
        var regPasswordInput = registerForm.querySelector('[name="password"]');
        var regConfirmInput = registerForm.querySelector('[name="confirm_password"]');
        var regTermsInput = registerForm.querySelector('[name="accept_terms"]');

        // Live validation & error clearing
        [loginEmailInput, loginPasswordInput].forEach(function (input) {
            if (!input) return;
            input.addEventListener("input", function () {
                clearFieldError(loginForm, input.name);
            });
            input.addEventListener("blur", function () {
                if (input.name === "email" && input.value) {
                    var r = Api.validateEmail(input.value);
                    if (!r.valid) setFieldError(loginForm, "email", r.message);
                }
            });
        });

        if (regPasswordInput) {
            regPasswordInput.addEventListener("input", function () {
                updatePasswordRulesUI(regPasswordInput.value);
                clearFieldError(registerForm, "password");
                if (regConfirmInput && regConfirmInput.value === regPasswordInput.value) {
                    clearFieldError(registerForm, "confirm_password");
                }
            });
        }

        [regNameInput, regPhoneInput, regEmailInput, regConfirmInput].forEach(function (input) {
            if (!input) return;
            input.addEventListener("input", function () {
                clearFieldError(registerForm, input.name);
            });
            input.addEventListener("blur", function () {
                if (!input.value && input.name !== "phone") return;
                if (input.name === "full_name") {
                    var nr = Api.validateFullName(input.value);
                    if (!nr.valid) setFieldError(registerForm, "full_name", nr.message);
                } else if (input.name === "email") {
                    var er = Api.validateEmail(input.value);
                    if (!er.valid) setFieldError(registerForm, "email", er.message);
                } else if (input.name === "phone") {
                    var pr = Api.validatePhone(input.value);
                    if (!pr.valid) setFieldError(registerForm, "phone", pr.message);
                } else if (input.name === "confirm_password" && regPasswordInput) {
                    if (input.value !== regPasswordInput.value) {
                        setFieldError(registerForm, "confirm_password", "Mật khẩu xác nhận không khớp");
                    }
                }
            });
        });

        if (regTermsInput) {
            regTermsInput.addEventListener("change", function () {
                clearFieldError(registerForm, "accept_terms");
            });
        }

        // Login submit
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            hideAlert(loginAlert);
            clearAllFieldErrors(loginForm);

            var values = {
                email: loginEmailInput ? loginEmailInput.value : "",
                password: loginPasswordInput ? loginPasswordInput.value : "",
            };
            var validation = Api.validateLoginForm(values);
            if (!validation.valid) {
                Object.keys(validation.errors).forEach(function (f) {
                    setFieldError(loginForm, f, validation.errors[f]);
                });
                var first = Object.keys(validation.errors)[0];
                var el = loginForm.querySelector('[name="' + first + '"]');
                if (el) el.focus();
                return;
            }

            setFormDisabled(loginForm, true);
            setButtonLoading(loginSubmitBtn, true, "ĐANG ĐĂNG NHẬP...", loginBtnText);

            try {
                var data = await Api.loginUser(validation.payload);
                var rememberMe = rememberInput ? rememberInput.checked : true;
                Api.saveAuthSession(data.access_token, data.user, rememberMe);

                showAlert(loginAlert, {
                    variant: "success",
                    title: "Đăng nhập thành công",
                    message: "Chào mừng " + data.user.full_name + "! Đang chuyển về trang chủ...",
                });

                window.setTimeout(function () {
                    window.location.href = redirectTarget;
                }, 450);
            } catch (err) {
                setFormDisabled(loginForm, false);
                setButtonLoading(loginSubmitBtn, false, "ĐANG ĐĂNG NHẬP...", loginBtnText);

                if (err && err.fieldErrors) {
                    Object.keys(err.fieldErrors).forEach(function (f) {
                        setFieldError(loginForm, f, err.fieldErrors[f]);
                    });
                }

                showAlert(loginAlert, {
                    variant: (err && err.variant) || "error",
                    title: (err && err.title) || "Đăng nhập thất bại",
                    message: (err && err.message) || "Vui lòng kiểm tra lại thông tin đăng nhập.",
                });
            }
        });

        // Register submit
        registerForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            hideAlert(registerAlert);
            clearAllFieldErrors(registerForm);

            var selectedRole = "CANDIDATE";
            roleInputs.forEach(function (r) {
                if (r.checked) selectedRole = r.value;
            });

            var values = {
                role: selectedRole,
                full_name: regNameInput ? regNameInput.value : "",
                phone: regPhoneInput ? regPhoneInput.value : "",
                email: regEmailInput ? regEmailInput.value : "",
                password: regPasswordInput ? regPasswordInput.value : "",
                confirm_password: regConfirmInput ? regConfirmInput.value : "",
                accept_terms: regTermsInput ? regTermsInput.checked : false,
            };

            var validation = Api.validateRegisterForm(values);
            if (!validation.valid) {
                Object.keys(validation.errors).forEach(function (f) {
                    setFieldError(registerForm, f, validation.errors[f]);
                });
                var first = Object.keys(validation.errors)[0];
                var el = registerForm.querySelector('[name="' + first + '"]');
                if (el) el.focus();
                return;
            }

            setFormDisabled(registerForm, true);
            setButtonLoading(registerSubmitBtn, true, "ĐANG TẠO TÀI KHOẢN...", registerBtnText);

            try {
                var user = await Api.registerUser(validation.payload);
                setFormDisabled(registerForm, false);
                setButtonLoading(registerSubmitBtn, false, "ĐANG TẠO TÀI KHOẢN...", registerBtnText);

                if (loginEmailInput) loginEmailInput.value = user.email;
                if (loginPasswordInput) loginPasswordInput.value = "";
                if (regPasswordInput) regPasswordInput.value = "";
                if (regConfirmInput) regConfirmInput.value = "";
                updatePasswordRulesUI("");
                hideAlert(registerAlert);

                showAlert(loginAlert, {
                    variant: "success",
                    title: "Đăng ký thành công!",
                    message:
                        "Tài khoản " +
                        Api.getRoleLabel(user.role).toLowerCase() +
                        " (" +
                        user.email +
                        ") đã được tạo. Vui lòng đăng nhập.",
                });

                applyMode("login", true);
            } catch (err) {
                setFormDisabled(registerForm, false);
                setButtonLoading(registerSubmitBtn, false, "ĐANG TẠO TÀI KHOẢN...", registerBtnText);

                if (err && err.fieldErrors) {
                    Object.keys(err.fieldErrors).forEach(function (f) {
                        setFieldError(registerForm, f, err.fieldErrors[f]);
                    });
                }

                var alertOpts = {
                    variant: (err && err.variant) || "error",
                    title: (err && err.title) || "Đăng ký thất bại",
                    message: (err && err.message) || "Không thể tạo tài khoản. Vui lòng thử lại.",
                };

                if (err && err.status === 409 && regEmailInput) {
                    alertOpts.actionText = "Chuyển sang đăng nhập với email này →";
                    alertOpts.onAction = function () {
                        if (loginEmailInput) loginEmailInput.value = regEmailInput.value.trim();
                        applyMode("login", true);
                    };
                }

                showAlert(registerAlert, alertOpts);
            }
        });

        checkExistingSession(loginAlert);
    }

    document.addEventListener("DOMContentLoaded", function () {
        initNavbarToggle();
        initPasswordToggles();
        initAuthForms();
    });
}());
