"""
Universe Router

Endpoints for searching items, systems, regions, and resolving locations.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from typing import Optional

from app.database import get_db
from app.cache import get_redis
from app.clients.esi_client import ESIClient
from app.services.universe_service import UniverseService


router = APIRouter()


async def get_universe_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> UniverseService:
    """Dependency to get UniverseService instance."""
    esi_client = ESIClient(redis)
    return UniverseService(db, esi_client)


@router.get("/search/items")
async def search_items(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, le=100, description="Maximum results"),
    universe_service: UniverseService = Depends(get_universe_service)
):
    """
    Autocomplete search for items by name.
    
    Returns results in React Select format: [{label, value}]
    
    Args:
        q: Search query (minimum 2 characters)
        limit: Maximum number of results (max 100)
    
    Returns:
        List of {label: item_name, value: type_id}
    
    Example:
        GET /universe/search/items?q=tritanium&limit=10
    """
    results = await universe_service.search_items(q, limit)
    
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.get("/search/systems")
async def search_systems(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, le=100, description="Maximum results"),
    universe_service: UniverseService = Depends(get_universe_service)
):
    """
    Autocomplete search for solar systems by name.
    
    Args:
        q: Search query (minimum 2 characters)
        limit: Maximum number of results (max 100)
    
    Returns:
        List of {label: "System Name (security)", value: system_id, security: float}
    
    Example:
        GET /universe/search/systems?q=jita
    """
    results = await universe_service.search_systems(q, limit)
    
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.get("/search/regions")
async def search_regions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, le=100, description="Maximum results"),
    universe_service: UniverseService = Depends(get_universe_service)
):
    """
    Search for regions by name.
    
    Args:
        q: Search query
        limit: Maximum results
    
    Returns:
        List of {label: region_name, value: region_id}
    
    Example:
        GET /universe/search/regions?q=forge
    """
    results = await universe_service.search_regions(q, limit)
    
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.get("/items/{type_id}")
async def get_item_details(
    type_id: int,
    universe_service: UniverseService = Depends(get_universe_service)
):
    """
    Get detailed information about an item.
    
    Args:
        type_id: Item type ID
    
    Returns:
        Item details including name, description, volume, market group, etc.
    
    Example:
        GET /universe/items/34
    """
    item = await universe_service.get_item_details(type_id)
    
    if not item:
        return {"error": "Item not found"}, 404
    
    return item


@router.get("/systems/{system_id}")
async def get_system_details(
    system_id: int,
    universe_service: UniverseService = Depends(get_universe_service)
):
    """
    Get detailed information about a solar system.
    
    Args:
        system_id: Solar system ID
    
    Returns:
        System details including name, security, region, constellation
    
    Example:
        GET /universe/systems/30000142
    """
    system = await universe_service.get_system_details(system_id)
    
    if not system:
        return {"error": "System not found"}, 404
    
    return system


@router.get("/stations/{station_id}")
async def resolve_station(
    station_id: int,
    universe_service: UniverseService = Depends(get_universe_service)
):
    """
    Resolve station or structure name.
    
    Works for both NPC stations (from SDE) and player structures (from ESI).
    
    Args:
        station_id: Station or structure ID
    
    Returns:
        Station details including name, solar system, type
    
    Example:
        GET /universe/stations/60003760
    """
    station = await universe_service.resolve_station(station_id)
    
    if not station:
        return {"error": "Station not found"}, 404
    
    return station
