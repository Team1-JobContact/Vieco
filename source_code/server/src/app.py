import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from src.config.settings import SERVER_DIR, settings
from src.config.database import engine
from src.config.frontend import FrontendFiles
import src.models  # noqa: F401 - Đăng ký model (schema do Alembic quản lý: alembic upgrade head)
from src.routes.core import router as core_router
from src.routes.admin import router as admin_router
from src.routes.auth import router as auth_router
from src.routes.candidate import router as candidate_router
from src.routes.catalog import router as catalog_router
from src.routes.company import admin_router as admin_company_router
from src.routes.company import employer_router as employer_company_router
from src.routes.company import media_router
from src.routes.job import admin_router as admin_job_router
from src.routes.job import employer_router as employer_job_router

# Tạo thư mục upload nếu chưa tồn tại
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Cấu hình CORS cho phép frontend HTML/JS gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([settings.FRONTEND_URL.rstrip("/"), *settings.CORS_ORIGINS])),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(candidate_router)
app.include_router(catalog_router)
app.include_router(employer_company_router)
app.include_router(admin_company_router)
app.include_router(media_router)
app.include_router(employer_job_router)
app.include_router(admin_job_router)

# Route kiểm tra kết nối API
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "success",
        "message": "JobContact Python Backend is active and running!",
        "database": "Not checked by this liveness endpoint"
    }

@app.get("/api/v1/ready")
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}


# Mount only the frontend, after every API route. CVs remain behind their API.
if settings.SERVE_FRONTEND:
    app.mount("/", FrontendFiles(directory=SERVER_DIR.parent / "client", html=True), name="frontend")


# Chạy trực tiếp: python src/app.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, reload=True)

