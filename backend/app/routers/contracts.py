"""
Contracts Router

Endpoints for fetching and appraising contracts.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from typing import Optional

from app.database import get_db
from app.cache import get_redis
from app.clients.esi_client import ESIClient
from app.services.contract_service import ContractService
from app.services.market_service import MarketService


router = APIRouter()


async def get_contract_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> ContractService:
    """Dependency to get ContractService instance."""
    esi_client = ESIClient(redis)
    market_service = MarketService(esi_client)
    return ContractService(db, esi_client, market_service)


async def get_access_token(
    request: Request,
    redis: Redis = Depends(get_redis)
) -> Optional[str]:
    """Get access token from session."""
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        return None
    
    from app.clients.token_manager import TokenManager
    
    session_data = await redis.get(f"session:{session_id}")
    if not session_data:
        return None
    
    import ast
    session = ast.literal_eval(session_data)
    character_id = session.get("character_id")
    
    if not character_id:
        return None
    
    token_manager = TokenManager(redis)
    return await token_manager.get_access_token(character_id)


@router.get("/public/{region_id}")
async def get_public_contracts(
    region_id: int,
    access_token: Optional[str] = Depends(get_access_token),
    contract_service: ContractService = Depends(get_contract_service)
):
    """
    Fetch public contracts in a region.
    
    Args:
        region_id: Region ID
    
    Returns:
        List of public contracts
    
    Example:
        GET /contracts/public/10000002
    """
    contracts = await contract_service.fetch_public_contracts(
        region_id=region_id,
        access_token=access_token
    )
    
    return {
        "region_id": region_id,
        "count": len(contracts),
        "contracts": contracts
    }


@router.get("/appraise/{contract_id}")
async def appraise_contract(
    contract_id: int,
    asking_price: float = Query(..., description="Contract asking price in ISK"),
    request: Request = None,
    access_token: Optional[str] = Depends(get_access_token),
    contract_service: ContractService = Depends(get_contract_service)
):
    """
    Appraise a contract using Jita Split methodology.
    
    Jita Split = (min_sell + max_buy) / 2 for each item
    
    Args:
        contract_id: Contract ID
        asking_price: Contract asking price (ISK)
    
    Returns:
        {
            "contract_id": int,
            "total_value": float,
            "asking_price": float,
            "profit": float,
            "profit_percent": float,
            "item_count": int,
            "top_items": [...]
        }
    
    Example:
        GET /contracts/appraise/12345?asking_price=1000000000
    """
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to appraise contracts"
        )
    
    appraisal = await contract_service.appraise_contract(
        contract_id=contract_id,
        asking_price=asking_price,
        access_token=access_token
    )
    
    if not appraisal:
        raise HTTPException(status_code=404, detail="Contract not found or has no items")
    
    return appraisal
