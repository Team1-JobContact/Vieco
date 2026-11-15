from fastapi import APIRouter, status
from src.schemas.auth import TokenResponse, UserResponse
from src.controllers import auth_controller as controller

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

router.add_api_route("/register", controller.register, methods=["POST"], response_model=UserResponse, status_code=status.HTTP_201_CREATED)
router.add_api_route("/login", controller.login, methods=["POST"], response_model=TokenResponse)
router.add_api_route("/logout", controller.logout, methods=["POST"])
router.add_api_route("/me", controller.me, methods=["GET"], response_model=UserResponse)
