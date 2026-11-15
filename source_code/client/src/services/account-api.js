window.ViecoAccountApi = {
    async submit(action, payload) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 15000);
        try {
            const response = await fetch(window.ViecoAuthApi.getApiBaseUrl() + "/auth/" + action, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload), signal: controller.signal
            });
            const body = await response.json();
            if (!response.ok) {
                const detail = typeof body.detail === "string" ? body.detail : "Thông tin không hợp lệ, vui lòng kiểm tra lại";
                throw new Error(detail);
            }
            return body;
        } finally {
            clearTimeout(timer);
        }
    }
};
