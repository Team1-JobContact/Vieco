const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

// Kiểm tra kết nối Backend khi tải trang
document.addEventListener("DOMContentLoaded", async () => {
    const statusBadge = document.getElementById("api-status");
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
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

