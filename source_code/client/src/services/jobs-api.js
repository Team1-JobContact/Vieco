window.ViecoJobsApi = {
    async list(query, page) {
        const params = new URLSearchParams({q: query || "", page: String(page || 1), page_size: "12"});
        const response = await fetch(window.ViecoAuthApi.getApiBaseUrl() + "/jobs?" + params);
        if (!response.ok) throw new Error("Không tải được danh sách việc làm");
        return response.json();
    },
    async get(id) {
        const response = await fetch(window.ViecoAuthApi.getApiBaseUrl() + "/jobs/" + encodeURIComponent(id));
        if (!response.ok) throw new Error("Tin tuyển dụng không còn hiển thị");
        return response.json();
    }
};
