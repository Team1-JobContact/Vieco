from fastapi import APIRouter, status
from src.schemas.company import AdminCompanyListResponse, AdminCompanyResponse, MyCompanyResponse
from src.controllers import company_controller as controller

employer_router = APIRouter(prefix="/api/v1/employer/company", tags=["Employer Company"])
admin_router = APIRouter(prefix="/api/v1/admin/companies", tags=["Admin Company"])

employer_router.add_api_route("", controller.get_my_company, methods=["GET"], response_model=MyCompanyResponse)
employer_router.add_api_route("", controller.create_my_company, methods=["POST"], response_model=MyCompanyResponse, status_code=status.HTTP_201_CREATED)
employer_router.add_api_route("", controller.update_my_company, methods=["PATCH"], response_model=MyCompanyResponse)
employer_router.add_api_route("/resubmit", controller.resubmit_my_company, methods=["POST"], response_model=MyCompanyResponse)
employer_router.add_api_route("/media", controller.get_my_media, methods=["GET"])
employer_router.add_api_route("/logo", controller.upload_logo, methods=["POST"])
employer_router.add_api_route("/logo", controller.delete_logo, methods=["DELETE"])
employer_router.add_api_route("/cover", controller.upload_cover, methods=["POST"])
employer_router.add_api_route("/cover", controller.delete_cover, methods=["DELETE"])
employer_router.add_api_route("/images", controller.upload_image, methods=["POST"], status_code=status.HTTP_201_CREATED)
employer_router.add_api_route("/images/{image_id}", controller.delete_image, methods=["DELETE"])
media_router = APIRouter(prefix="/api/v1/media", tags=["Media"])
media_router.add_api_route("/company/{file_name}", controller.serve_company_media, methods=["GET"])
admin_router.add_api_route("", controller.list_companies, methods=["GET"], response_model=AdminCompanyListResponse)
admin_router.add_api_route("/{company_id}", controller.get_company, methods=["GET"], response_model=AdminCompanyResponse)
admin_router.add_api_route("/{company_id}/approve", controller.approve_company, methods=["POST"], response_model=AdminCompanyResponse)
admin_router.add_api_route("/{company_id}/reject", controller.reject_company, methods=["POST"], response_model=AdminCompanyResponse)
admin_router.add_api_route("/{company_id}/verification", controller.verify_company, methods=["PUT"], response_model=AdminCompanyResponse)
