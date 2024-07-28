from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/healthz/", tags=["health"])
async def get_health() -> HealthResponse:
    return HealthResponse(status="health")
