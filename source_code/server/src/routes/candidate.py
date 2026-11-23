from fastapi import APIRouter, status
from src.schemas.candidate import CVListResponse, CVResponse, ProfileResponse
from src.schemas.cv_builder import CVAIResponse, CVBuilderResponse
from src.schemas.job_ai import CVTailorResponse, JobMatchResponse
from src.controllers import candidate_controller as controller
from src.controllers import profile_history_controller as history

router = APIRouter(prefix="/api/v1/candidates/me", tags=["Candidate"])

router.add_api_route("/profile", controller.get_profile, methods=["GET"], response_model=ProfileResponse)
router.add_api_route("/profile", controller.create_profile, methods=["POST"], response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
router.add_api_route("/profile", controller.update_profile, methods=["PATCH"], response_model=ProfileResponse)
router.add_api_route("/profile", controller.delete_profile, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT)
router.add_api_route("/cvs", controller.list_cvs, methods=["GET"], response_model=CVListResponse)
router.add_api_route("/cvs", controller.upload_cv, methods=["POST"], response_model=CVResponse, status_code=status.HTTP_201_CREATED)
# Trình tạo CV trực tuyến: CV lưu dạng PDF kèm nội dung để mở lại chỉnh sửa; AI tạo nội dung từ thông tin tự nhập.
router.add_api_route("/cvs/builder", controller.create_builder_cv, methods=["POST"], response_model=CVResponse, status_code=status.HTTP_201_CREATED)
router.add_api_route("/cvs/builder/ai", controller.generate_cv_with_ai, methods=["POST"], response_model=CVAIResponse)
# AI theo tin tuyển dụng: chấm điểm CV phù hợp và tối ưu CV (kết quả mở trong trình tạo CV, chưa lưu).
router.add_api_route("/job-match", controller.match_job, methods=["POST"], response_model=JobMatchResponse)
router.add_api_route("/cvs/builder/tailor", controller.tailor_cv, methods=["POST"], response_model=CVTailorResponse)
router.add_api_route("/cvs/{cv_id}/builder", controller.get_builder_cv, methods=["GET"], response_model=CVBuilderResponse)
router.add_api_route("/cvs/{cv_id}/builder", controller.update_builder_cv, methods=["PUT"], response_model=CVResponse)
router.add_api_route("/cvs/{cv_id}/download", controller.download_cv, methods=["GET"])
router.add_api_route("/cvs/{cv_id}/default", controller.set_default_cv, methods=["PATCH"], response_model=CVResponse)
router.add_api_route("/cvs/{cv_id}", controller.delete_cv, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT)
router.add_api_route("/history", history.history, methods=["GET"])
router.add_api_route("/avatar", controller.upload_avatar, methods=["POST"])
router.add_api_route("/avatar", controller.delete_avatar, methods=["DELETE"])
router.add_api_route("/history/{kind}", history.create_entry, methods=["POST"], status_code=201)
router.add_api_route("/history/{kind}/{entry_id}", history.update_entry, methods=["PUT"])
router.add_api_route("/history/{kind}/{entry_id}", history.delete_entry, methods=["DELETE"], status_code=204)
