from fastapi import APIRouter
from src.controllers import admin_controller as controller

router = APIRouter(prefix="/api/v1", tags=["Administration"])
router.add_api_route("/admin/users", controller.list_users, methods=["GET"])
router.add_api_route("/admin/users/{user_id}", controller.user_detail, methods=["GET"])
router.add_api_route("/admin/users/{user_id}/status", controller.update_user_status, methods=["PATCH"])
router.add_api_route("/admin/categories", controller.list_categories, methods=["GET"])
router.add_api_route("/admin/categories/{kind}/{category_id}", controller.update_category, methods=["PATCH"])
router.add_api_route("/admin/audit-logs", controller.list_audit_logs, methods=["GET"])
router.add_api_route("/admin/pages", controller.list_pages, methods=["GET"])
router.add_api_route("/admin/pages/{page_id}", controller.update_page, methods=["PATCH"])
router.add_api_route("/pages/{slug}", controller.public_page, methods=["GET"])
router.add_api_route("/admin/upload-settings", controller.list_upload_settings, methods=["GET"])
router.add_api_route("/admin/upload-settings/{key}", controller.update_upload_setting, methods=["PATCH"])
