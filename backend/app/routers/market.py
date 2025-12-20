"""
Market Router

Endpoints for market data, orders, and arbitrage analysis.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from typing import Optional

from app.database import get_db
from app.cache import get_redis
from app.clients.esi_client import ESIClient
from app.services.market_service import MarketService


router = APIRouter()


async def get_market_service(redis: Redis = Depends(get_redis)) -> MarketService:
    """Dependency to get MarketService instance."""
    esi_client = ESIClient(redis)
    return MarketService(esi_client)


@router.get("/orders")
async def get_market_orders(
    region_id: int = Query(..., description="Region ID"),
    type_id: Optional[int] = Query(None, description="Item type ID filter"),
    order_type: Optional[str] = Query(None, description="'buy' or 'sell' filter"),
    market_service: MarketService = Depends(get_market_service)
):
    """
    Fetch market orders for a region.
    
    Args:
        region_id: EVE region ID (e.g., 10000002 for The Forge/Jita)
        type_id: Optional item type ID to filter
        order_type: Optional 'buy' or 'sell' filter
    
    Returns:
        List of market orders with price, volume, location, etc.
    
    Example:
        GET /market/orders?region_id=10000002&type_id=34
    """
    orders = await market_service.fetch_market_orders(
        region_id=region_id,
        type_id=type_id,
        order_type=order_type
    )
    
    return {
        "region_id": region_id,
        "type_id": type_id,
        "order_type": order_type,
        "count": len(orders),
        "orders": orders
    }


@router.get("/prices/{type_id}")
async def get_best_prices(
    type_id: int,
    region_id: int = Query(10000002, description="Region ID (default: The Forge)"),
    market_service: MarketService = Depends(get_market_service)
):
    """
    Get best buy and sell prices for an item in a region.
    
    Args:
        type_id: Item type ID
        region_id: Region ID (defaults to The Forge/Jita)
    
    Returns:
        {
            "best_buy": float,
            "best_sell": float,
            "buy_volume": int,
            "sell_volume": int
        }
    
    Example:
        GET /market/prices/34?region_id=10000002
    """
    prices = await market_service.get_best_prices(region_id, type_id)
    
    return {
        "type_id": type_id,
        "region_id": region_id,
        **prices
    }


@router.get("/arbitrage")
async def calculate_arbitrage(
    region_a: int = Query(..., description="Source region ID"),
    region_b: int = Query(..., description="Destination region ID"),
    min_volume: int = Query(1000, description="Minimum order volume"),
    min_profit_percent: float = Query(5.0, description="Minimum profit percentage"),
    market_service: MarketService = Depends(get_market_service)
):
    """
    Calculate arbitrage opportunities between two regions.
    
    Finds items where buying in region_a and selling in region_b 
    yields profit above the minimum threshold.
    
    Args:
        region_a: Source region ID (buy from here)
        region_b: Destination region ID (sell here)
        min_volume: Minimum order volume to consider
        min_profit_percent: Minimum profit percentage threshold
    
    Returns:
        List of arbitrage opportunities sorted by profit descending
    
    Example:
        GET /market/arbitrage?region_a=10000002&region_b=10000043&min_profit_percent=10
    """
    opportunities = await market_service.calculate_arbitrage(
        region_a=region_a,
        region_b=region_b,
        min_volume=min_volume,
        min_profit_percent=min_profit_percent
    )
    
    return {
        "source_region": region_a,
        "destination_region": region_b,
        "min_volume": min_volume,
        "min_profit_percent": min_profit_percent,
        "count": len(opportunities),
        "opportunities": opportunities
    }


@router.post("/profit/calculate")
async def calculate_profit(
    buy_price: float,
    sell_price: float,
    accounting_level: int = 0,
    broker_relations_level: int = 0,
    standings: float = 0.0,
    market_service: MarketService = Depends(get_market_service)
):
    """
    Calculate net profit with tax and broker fee calculations.
    
    Uses EVE Online formulas:
    - Sales Tax: 8% base, reduced by 11% per Accounting level
    - Broker Fee: 3% base, reduced by 0.3% per Broker Relations level
    
    Args:
        buy_price: Purchase price (ISK)
        sell_price: Sale price (ISK)
        accounting_level: Accounting skill level (0-5)
        broker_relations_level: Broker Relations skill level (0-5)
        standings: Corporation standings (0.0 to 10.0)
    
    Returns:
        Detailed profit breakdown including taxes, fees, net profit, and ROI
    
    Example:
        POST /market/profit/calculate
        {
            "buy_price": 1000000,
            "sell_price": 1200000,
            "accounting_level": 5,
            "broker_relations_level": 5
        }
    """
    result = market_service.calculate_net_profit(
        buy_price=buy_price,
        sell_price=sell_price,
        accounting_level=accounting_level,
        broker_relations_level=broker_relations_level,
        standings=standings
    )
    
    return result
