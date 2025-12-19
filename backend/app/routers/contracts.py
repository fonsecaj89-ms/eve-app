from fastapi import APIRouter, BackgroundTasks
from app.logger import structlog
from app.services.contracts import contract_service, JITA_REGION_ID

logger = structlog.get_logger()
router = APIRouter(prefix="/api/contracts", tags=["Contracts"])

@router.get("/public")
async def get_public_contracts(background_tasks: BackgroundTasks, region_id: int = JITA_REGION_ID):
    """
    Fetch public contracts. Triggers update in background if needed (not implemented here fully, just fetches).
    """
    logger.info("get_public_contracts_request", region_id=region_id)
    # For now, synchronous fetch (might be slow if pages > 1).
    # Ideally we start a background task to sync and return cached stats?
    # Simple implementation: Return list from ESI directly or cache?
    # Service implementation `fetch_public_contracts` does ESI -> Redis.
    # We'll return the result of that.
    return await contract_service.fetch_public_contracts(region_id)

@router.get("/{contract_id}/valuation")
async def get_contract_valuation(contract_id: int):
    logger.info("get_contract_valuation_request", contract_id=contract_id)
    return await contract_service.value_contract(contract_id)
