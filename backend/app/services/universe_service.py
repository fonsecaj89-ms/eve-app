"""
Universe Service

Handles item and location resolution from SDE database.
Provides autocomplete search and station/structure lookups.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
from app.models.sde import InvType, StaStation, MapSolarSystem, MapRegion
from app.clients.esi_client import ESIClient


class UniverseService:
    """
    Service for universe data (items, stations, systems).
    """
    
    def __init__(self, db: AsyncSession, esi_client: Optional[ESIClient] = None):
        self.db = db
        self.esi_client = esi_client
    
    async def search_items(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search for items by name (autocomplete).
        
        Args:
            query: Search string
            limit: Maximum results
        
        Returns:
            List of {label: str, value: int} for React Select
        """
        stmt = select(InvType).where(
            InvType.type_name.ilike(f"%{query}%")
        ).where(
            InvType.published == True
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        return [
            {
                "label": item.type_name,
                "value": item.type_id
            }
            for item in items
        ]
    
    async def get_item_details(self, type_id: int) -> Optional[dict]:
        """
        Get full item details.
        
        Args:
            type_id: Item type ID
        
        Returns:
            Item details dictionary or None
        """
        stmt = select(InvType).where(InvType.type_id == type_id)
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        return {
            "type_id": item.type_id,
            "name": item.type_name,
            "description": item.description,
            "volume": item.volume,
            "portion_size": item.portion_size,
            "market_group_id": item.market_group_id,
            "published": item.published
        }
    
    async def resolve_station(self, station_id: int) -> Optional[dict]:
        """
        Resolve station name from NPC station database or ESI for structures.
        
        Args:
            station_id: Station or structure ID
        
        Returns:
            Station details or None
        """
        # Try NPC station first
        if station_id < 1000000000000:  # NPC stations have lower IDs
            stmt = select(StaStation).where(StaStation.station_id == station_id)
            result = await self.db.execute(stmt)
            station = result.scalar_one_or_none()
            
            if station:
                return {
                    "station_id": station.station_id,
                    "name": station.station_name,
                    "solar_system_id": station.solar_system_id,
                    "type": "npc_station"
                }
        
        # Try player structure via ESI
        if self.esi_client:
            try:
                # This requires esi-universe.read_structures.v1 scope
                data = await self.esi_client.get(f"/universe/structures/{station_id}/")
                return {
                    "station_id": station_id,
                    "name": data.get("name", f"Structure {station_id}"),
                    "solar_system_id": data.get("solar_system_id"),
                    "type": "player_structure"
                }
            except Exception as e:
                print(f"❌ Failed to resolve structure {station_id}: {e}")
        
        return None
    
    async def search_systems(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search for solar systems by name (autocomplete).
        
        Args:
            query: Search string
            limit: Maximum results
        
        Returns:
            List of {label: str, value: int, security: float}
        """
        stmt = select(MapSolarSystem).where(
            MapSolarSystem.solar_system_name.ilike(f"%{query}%")
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        systems = result.scalars().all()
        
        return [
            {
                "label": f"{system.solar_system_name} ({system.security:.1f})",
                "value": system.solar_system_id,
                "security": float(system.security) if system.security else 0.0
            }
            for system in systems
        ]
    
    async def get_system_details(self, system_id: int) -> Optional[dict]:
        """
        Get solar system details.
        
        Args:
            system_id: Solar system ID
        
        Returns:
            System details or None
        """
        stmt = select(MapSolarSystem).where(
            MapSolarSystem.solar_system_id == system_id
        )
        result = await self.db.execute(stmt)
        system = result.scalar_one_or_none()
        
        if not system:
            return None
        
        return {
            "system_id": system.solar_system_id,
            "name": system.solar_system_name,
            "security": float(system.security) if system.security else 0.0,
            "security_status": system.security_status,
            "region_id": system.region_id,
            "constellation_id": system.constellation_id
        }
    
    async def search_regions(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search for regions by name.
        
        Args:
            query: Search string
            limit: Maximum results
        
        Returns:
            List of {label: str, value: int}
        """
        stmt = select(MapRegion).where(
            MapRegion.region_name.ilike(f"%{query}%")
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        regions = result.scalars().all()
        
        return [
            {
                "label": region.region_name,
                "value": region.region_id
            }
            for region in regions
        ]
