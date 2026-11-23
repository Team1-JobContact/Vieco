from fastapi import APIRouter, status
from src.schemas.job import JobListResponse, JobResponse
from src.schemas.job_ai import JobDraftResponse
from src.controllers import job_controller as controller

employer_router = APIRouter(prefix="/api/v1/employer/jobs", tags=["Employer Jobs"])
admin_router = APIRouter(prefix="/api/v1/admin/jobs", tags=["Admin Jobs"])

employer_router.add_api_route("", controller.list_my_jobs, methods=["GET"], response_model=JobListResponse)
employer_router.add_api_route("", controller.create_job, methods=["POST"], response_model=JobResponse, status_code=status.HTTP_201_CREATED)
employer_router.add_api_route("/ai-draft", controller.draft_job_with_ai, methods=["POST"], response_model=JobDraftResponse)
employer_router.add_api_route("/{job_id}", controller.get_my_job, methods=["GET"], response_model=JobResponse)
employer_router.add_api_route("/{job_id}", controller.update_job, methods=["PATCH"], response_model=JobResponse)
employer_router.add_api_route("/{job_id}/submit", controller.submit_job, methods=["POST"], response_model=JobResponse)
employer_router.add_api_route("/{job_id}/close", controller.close_job, methods=["POST"], response_model=JobResponse)
employer_router.add_api_route("/{job_id}/reopen", controller.reopen_job, methods=["POST"], response_model=JobResponse)
employer_router.add_api_route("/{job_id}/extend", controller.extend_job, methods=["POST"], response_model=JobResponse)
employer_router.add_api_route("/{job_id}", controller.delete_draft_job, methods=["DELETE"])
admin_router.add_api_route("", controller.admin_list_jobs, methods=["GET"], response_model=JobListResponse)
admin_router.add_api_route("/{job_id}", controller.admin_get_job, methods=["GET"], response_model=JobResponse)
admin_router.add_api_route("/{job_id}/approve", controller.approve_job, methods=["POST"], response_model=JobResponse)
admin_router.add_api_route("/{job_id}/reject", controller.reject_job, methods=["POST"], response_model=JobResponse)
admin_router.add_api_route("/{job_id}/remove", controller.remove_job, methods=["POST"], response_model=JobResponse)
