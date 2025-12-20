"""
Character Router

Endpoints for character-specific data: wallet, skills, transactions.
Requires authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis

from app.cache import get_redis
from app.clients.esi_client import ESIClient
from app.clients.token_manager import TokenManager


router = APIRouter()


async def get_current_character(
    request: Request,
    redis: Redis = Depends(get_redis)
) -> dict:
    """
    Dependency to get current authenticated character.
    
    Returns:
        {character_id: int, character_name: str}
    
    Raises:
        HTTPException: If not authenticated
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_data = await redis.get(f"session:{session_id}")
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")
    
    import ast
    return ast.literal_eval(session_data)


@router.get("/wallet")
async def get_wallet_balance(
    character: dict = Depends(get_current_character),
    redis: Redis = Depends(get_redis)
):
    """
    Get character wallet balance.
    
    Requires scope: esi-wallet.read_character_wallet.v1
    
    Returns:
        {
            "character_id": int,
            "balance": float
        }
    
    Example:
        GET /character/wallet
    """
    character_id = character["character_id"]
    
    # Get access token
    token_manager = TokenManager(redis)
    access_token = await token_manager.get_access_token(character_id)
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token not found")
    
    # Fetch wallet from ESI
    esi_client = ESIClient(redis)
    
    try:
        balance = await esi_client.get(
            f"/characters/{character_id}/wallet/",
            access_token=access_token
        )
        
        return {
            "character_id": character_id,
            "balance": float(balance)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch wallet: {str(e)}")


@router.get("/skills")
async def get_character_skills(
    character: dict = Depends(get_current_character),
    redis: Redis = Depends(get_redis)
):
    """
    Get character skills.
    
    Requires scope: esi-skills.read_skills.v1
    
    Returns:
        {
            "total_sp": int,
            "skills": [...]
        }
    
    Example:
        GET /character/skills
    """
    character_id = character["character_id"]
    
    # Get access token
    token_manager = TokenManager(redis)
    access_token = await token_manager.get_access_token(character_id)
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token not found")
    
    # Fetch skills from ESI
    esi_client = ESIClient(redis)
    
    try:
        data = await esi_client.get(
            f"/characters/{character_id}/skills/",
            access_token=access_token
        )
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch skills: {str(e)}")


@router.get("/transactions")
async def get_character_transactions(
    character: dict = Depends(get_current_character),
    redis: Redis = Depends(get_redis)
):
    """
    Get character market transactions (last 90 days).
    
    Requires scope: esi-wallet.read_character_wallet.v1
    
    Returns:
        List of transaction dictionaries
    
    Example:
        GET /character/transactions
    """
    character_id = character["character_id"]
    
    # Get access token
    token_manager = TokenManager(redis)
    access_token = await token_manager.get_access_token(character_id)
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token not found")
    
    # Fetch transactions from ESI
    esi_client = ESIClient(redis)
    
    try:
        data = await esi_client.get(
            f"/characters/{character_id}/wallet/transactions/",
            access_token=access_token
        )
        
        return {
            "character_id": character_id,
            "count": len(data),
            "transactions": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")
