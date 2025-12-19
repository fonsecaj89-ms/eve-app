import asyncio
from typing import List, Dict
from sqlmodel import Session, select, delete
from app.db.engine import engine
from app.models.market import MarketOrder
from app.services.esi import esi_client
from app.logger import structlog
from datetime import datetime

logger = structlog.get_logger()

class MarketService:
    async def fetch_region_orders(self, region_id: int):
        """
        Fetches all orders for a region (using pagination) and updates Postgres.
        Iterates region markets with delay as requested (though prompt said "Iterate all markets in the region using delay logic").
        ESI endpoint /markets/{region_id}/orders/ covers the whole region.
        Pagination handles the loop.
        """
        logger.info("market_scan_start", region_id=region_id)
        endpoint = f"/markets/{region_id}/orders/"
        params = {"order_type": "all"}
        
        try:
            orders_data = await esi_client.get_all_pages(endpoint, params=params)
            logger.info("market_scan_fetched", count=len(orders_data))
            
            # Bulk processing
            # We should probably clear old orders for this region or upsert?
            # Simplest for "Snapshot" data is Delete-Insert for the region logic, 
            # OR upsert if we track history (but history bloats).
            # "Snapshot data only" implies current state.
            
            with Session(engine) as session:
                # Delete existing orders for this region to remove filled/cancelled ones
                # This is a brute-force snapshot update.
                session.exec(delete(MarketOrder).where(MarketOrder.region_id == region_id))
                
                new_orders = []
                for o in orders_data:
                    order = MarketOrder(
                        order_id=o["order_id"],
                        type_id=o["type_id"],
                        location_id=o["location_id"],
                        region_id=region_id,
                        system_id=o["system_id"],
                        is_buy_order=o["is_buy_order"],
                        price=o["price"],
                        volume_remain=o["volume_remain"],
                        volume_total=o["volume_total"],
                        min_volume=o["min_volume"],
                        issued=datetime.fromisoformat(o["issued"].replace("Z", "+00:00")),
                        duration=o["duration"],
                        range=o["range"]
                    )
                    new_orders.append(order)
                
                # Bulk insert
                session.add_all(new_orders)
                session.commit()
                
            logger.info("market_scan_complete", region_id=region_id, saved=len(new_orders))
            
        except Exception as e:
            logger.error("market_scan_failed", region_id=region_id, error=str(e))
            raise e

    async def get_arbitrage_opportunities(self, regions: List[int] = None) -> List[Dict]:
        """
        Calculates arbitrage based on local DB snapshot.
        Global Scan: Query PostgreSQL/Redis snapshot data only.
        """
        # Logic: Find items where MAX(Buy) > MIN(Sell) across regions?
        # Or specifically Transport Arbitrage: Buy at A (Sell Order), Sell at B (Buy Order).
        # "Profit Algorithm: Sort by Profit %. Input: Buy/Sell Station, Item, Tax Rate."
        
        # Simple Global Scan implementation:
        # Find pairs of orders: Sell Order (Source) -> Buy Order (Destination)
        # Check Profit > 0.
        
        # This is a heavy Query. SQL is best for this.
        # Self-join on type_id.
        
        query = """
        SELECT 
            s.type_id,
            s.price as buy_price,
            s.location_id as source_location,
            s.region_id as source_region,
            b.price as sell_price,
            b.location_id as dest_location,
            b.region_id as dest_region,
            (b.price - s.price) as gross_margin,
            ((b.price - s.price) / s.price) * 100 as roi
        FROM market_orders s
        JOIN market_orders b ON s.type_id = b.type_id
        WHERE s.is_buy_order = false  -- We buy from a Sell Order
          AND b.is_buy_order = true   -- We sell to a Buy Order
          AND b.price > s.price       -- Basic filter
          AND s.volume_remain > 0
          AND b.volume_remain > 0
        ORDER BY roi DESC
        LIMIT 50;
        """
        
        with Session(engine) as session:
            results = session.exec(text(query)).all()
            
            opportunities = []
            for row in results:
                # Convert raw row to dict (tuple in sqlalchemy core)
                # row fields map to selection order
                opportunities.append({
                    "type_id": row[0],
                    "buy_price": row[1],
                    "source": row[2],
                    "source_region": row[3],
                    "sell_price": row[4],
                    "destination": row[5],
                    "dest_region": row[6],
                    "margin": row[7],
                    "roi": round(row[8], 2)
                })
        
        return opportunities

    async def get_min_sell_price(self, region_id: int, type_id: int) -> float:
        """
        Get the lowest sell price for an item in a region from local DB.
        """
        query = select(MarketOrder.price).where(
            MarketOrder.region_id == region_id,
            MarketOrder.type_id == type_id,
            MarketOrder.is_buy_order == False
        ).order_by(MarketOrder.price.asc()).limit(1)
        
        with Session(engine) as session:
            price = session.exec(query).first()
            return price if price else 0.0

market_service = MarketService()
