from fastapi import APIRouter, BackgroundTasks, Query
from typing import List
from app.services.market import market_service
from app.logger import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/market", tags=["Market"])

@router.post("/scan/{region_id}")
async def scan_region(region_id: int, background_tasks: BackgroundTasks):
    """
    Trigger a background scan for a region.
    """
    background_tasks.add_task(market_service.fetch_region_orders, region_id)
    return {"status": "started", "region_id": region_id}

@router.get("/arbitrage/global")
async def global_arbitrage():
    """
    Get top 50 global arbitrage opportunities from snapshot.
    """
    return await market_service.get_arbitrage_opportunities()
