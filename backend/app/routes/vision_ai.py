from fastapi import APIRouter

from ..services.vision_product_service import capabilities

router = APIRouter(prefix="/api/vision-ai", tags=["vision-ai"])


@router.get("/capabilities")
def get_vision_ai_capabilities():
    return capabilities()
