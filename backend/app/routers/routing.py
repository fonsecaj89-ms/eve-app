"""
Routing Router

Endpoints for calculating routes between solar systems using Neo4j.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.graph import get_graph
from app.services.route_service import RouteService


router = APIRouter()


class RouteRequest(BaseModel):
    """Request model for route calculation."""
    start_id: int
    end_id: int
    security_preference: str = "shortest"  # 'safest', 'shortest', or 'custom'


@router.post("/calculate")
async def calculate_route(
    request: RouteRequest,
    driver = Depends(get_graph)
):
    """
    Calculate optimal route between two solar systems.
    
    Uses weighted Dijkstra pathfinding with security-based weights:
    - Shortest: All jumps equal weight
    - Safest: Heavy penalties for low/null sec
    - Custom: Moderate penalties
    
    Args:
        request: RouteRequest with start_id, end_id, security_preference
    
    Returns:
        {
            "waypoints": ["System 1", "System 2", ...],
            "system_ids": [id1, id2, ...],
            "jumps": int,
            "risk_score": float,
            "route_type": str
        }
    
    Example:
        POST /routing/calculate
        {
            "start_id": 30000142,
            "end_id": 30002187,
            "security_preference": "safest"
        }
    """
    route_service = RouteService(driver)
    
    result = await route_service.calculate_route(
        start_id=request.start_id,
        end_id=request.end_id,
        security_preference=request.security_preference
    )
    
    if not result:
        return {
            "error": "No route found",
            "start_id": request.start_id,
            "end_id": request.end_id
        }, 404
    
    return result


@router.get("/neighbors/{system_id}")
async def get_system_neighbors(
    system_id: int,
    driver = Depends(get_graph)
):
    """
    Get all systems directly connected to a given system.
    
    Args:
        system_id: Solar system ID
    
    Returns:
        List of neighboring system details
    
    Example:
        GET /routing/neighbors/30000142
    """
    route_service = RouteService(driver)
    neighbors = await route_service.get_system_neighbors(system_id)
    
    return {
        "system_id": system_id,
        "count": len(neighbors),
        "neighbors": neighbors
    }
