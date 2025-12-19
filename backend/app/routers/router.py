from fastapi import APIRouter, BackgroundTasks
from app.services.router import router_service
from app.logger import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/routes", tags=["Routing"])

@router.get("/")
async def get_route(origin: int, destination: int):
    logger.info("get_route_request", origin=origin, destination=destination)
    return await router_service.get_route(origin, destination)

@router.post("/update_safety")
async def update_safety(background_tasks: BackgroundTasks):
    logger.info("update_safety_request")
    background_tasks.add_task(router_service.update_safety_data)
    return {"status": "Safety update triggered"}
