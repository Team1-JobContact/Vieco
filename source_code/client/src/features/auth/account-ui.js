document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const action = params.get("action") || "forgot-password";
    const token = params.get("token");
    // Keep one-use secrets out of the visible URL after reading them.
    if (token) history.replaceState(null, "", window.location.pathname + "?action=" + encodeURIComponent(action));
    const form = document.getElementById("account-form");
    const title = document.getElementById("account-title");
    const message = document.getElementById("account-message");
    const button = document.getElementById("account-submit");
    const email = form.elements.email;
    const password = form.elements.password;
    if (!["verify-email", "reset-password", "forgot-password"].includes(action) ||
        (action !== "forgot-password" && !token)) {
        message.textContent = "Liên kết không hợp lệ";
        form.hidden = true;
        return;
    }
    title.textContent = action === "verify-email" ? "Xác thực email" : action === "reset-password" ? "Đặt lại mật khẩu" : "Quên mật khẩu";
    document.getElementById("email-field").hidden = action !== "forgot-password";
    email.disabled = action !== "forgot-password";
    password.disabled = action !== "reset-password";
    document.getElementById("password-field").hidden = action !== "reset-password";
    button.textContent = action === "verify-email" ? "Xác thực email" : action === "reset-password" ? "Đổi mật khẩu" : "Gửi email";
    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        if (button.disabled) return;
        if (action === "reset-password") {
            const validation = window.ViecoAuthApi.validatePassword(password.value);
            if (!validation.valid) { message.textContent = validation.message; return; }
        }
        button.disabled = true;
        try {
            const payload = action === "forgot-password" ? {email: email.value.trim()} :
                action === "verify-email" ? {token} : {token, password: password.value};
            const result = await window.ViecoAccountApi.submit(action, payload);
            message.textContent = result.message;
            if (action === "reset-password") window.ViecoAuthApi.clearAuthSession();
            form.hidden = true;
        } catch (error) {
            message.textContent = error.message || "Không kết nối được máy chủ";
        } finally {
            button.disabled = false;
        }
    });
});
