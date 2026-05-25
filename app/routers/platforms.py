"""平台列表 API。"""

from fastapi import APIRouter

from app.models.schemas import PlatformInfo
from app.services.platform_registry import get_registry

router = APIRouter(prefix="/api")


@router.get("/platforms", response_model=list[PlatformInfo])
async def list_platforms() -> list[dict]:
    return [s.to_dict() for s in get_registry()]