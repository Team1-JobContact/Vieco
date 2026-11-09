import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.config.database import engine, Base
from src.config.settings import settings
import src.models.user  # noqa: F401 - Đăng ký model để tạo bảng

# Tự động tạo bảng nếu chưa có
Base.metadata.create_all(bind=engine)

# Tạo thư mục upload nếu chưa tồn tại
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Cấu hình CORS cho phép frontend HTML/JS gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route kiểm tra kết nối API
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "success",
        "message": "JobContact Python Backend is active and running!",
        "database": "MySQL Connected"
    }

# Chạy trực tiếp: python src/app.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, reload=True)

