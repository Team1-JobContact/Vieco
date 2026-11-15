from fastapi import APIRouter
from src.controllers import catalog_controller as controller

router = APIRouter(prefix="/api/v1/categories", tags=["Catalog"])

router.add_api_route("", controller.get_categories, methods=["GET"])
