from fastapi import APIRouter, BackgroundTasks
from app.services.router import router_service

router = APIRouter(prefix="/api/routes", tags=["Routing"])

@router.get("/")
async def get_route(origin: int, destination: int):
    return await router_service.get_route(origin, destination)

@router.post("/update_safety")
async def update_safety(background_tasks: BackgroundTasks):
    background_tasks.add_task(router_service.update_safety_data)
    return {"status": "Safety update triggered"}
