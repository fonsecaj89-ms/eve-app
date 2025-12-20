"""
Contract Service

Handles contract appraisal using "Jita Split" methodology.
Jita Split = (min_sell + max_buy) / 2 for each item in Jita (The Forge)
"""

from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.clients.esi_client import ESIClient
from app.models.sde import InvType
from app.services.market_service import MarketService


class ContractItemAppraisal(BaseModel):
    """Appraisal for a single item in a contract."""
    type_id: int
    name: str
    quantity: int
    unit_price: float  # Jita Split price
    total_value: float


class ContractAppraisal(BaseModel):
    """Complete contract appraisal."""
    contract_id: int
    total_value: float
    asking_price: float
    profit: float
    profit_percent: float
    item_count: int
    top_items: list[ContractItemAppraisal]  # Top 5 by value


class ContractService:
    """
    Service for contract analysis and appraisal.
    """
    
    # The Forge (Jita's region)
    JITA_REGION_ID = 10000002
    
    def __init__(
        self,
        db: AsyncSession,
        esi_client: ESIClient,
        market_service: MarketService
    ):
        self.db = db
        self.esi_client = esi_client
        self.market_service = market_service
    
    async def fetch_contract_items(
        self,
        contract_id: int,
        access_token: str
    ) -> list[dict]:
        """
        Fetch items in a contract from ESI.
        
        Args:
            contract_id: Contract ID
            access_token: OAuth access token
        
        Returns:
            List of contract item dictionaries
        """
        try:
            data = await self.esi_client.get(
                f"/contracts/public/items/{contract_id}/",
                access_token=access_token
            )
            return data
        except Exception as e:
            print(f"❌ Failed to fetch contract items for {contract_id}: {e}")
            return []
    
    async def calculate_jita_split(self, type_id: int) -> float:
        """
        Calculate Jita Split price for an item.
        
        Jita Split = (min_sell + max_buy) / 2
        
        Args:
            type_id: Item type ID
        
        Returns:
            Jita Split price (ISK)
        """
        try:
            prices = await self.market_service.get_best_prices(
                self.JITA_REGION_ID,
                type_id
            )
            
            best_buy = prices.get("best_buy")
            best_sell = prices.get("best_sell")
            
            if best_buy is not None and best_sell is not None:
                return (best_buy + best_sell) / 2
            elif best_sell is not None:
                # If no buy orders, use sell price
                return best_sell
            elif best_buy is not None:
                # If no sell orders, use buy price
                return best_buy
            else:
                # No market data
                return 0.0
                
        except Exception as e:
            print(f"❌ Failed to calculate Jita Split for type {type_id}: {e}")
            return 0.0
    
    async def appraise_contract(
        self,
        contract_id: int,
        asking_price: float,
        access_token: str
    ) -> Optional[ContractAppraisal]:
        """
        Appraise a contract using Jita Split methodology.
        
        Args:
            contract_id: Contract ID
            asking_price: Contract asking price (ISK)
            access_token: OAuth access token
        
        Returns:
            ContractAppraisal with value breakdown
        """
        # Fetch contract items
        items = await self.fetch_contract_items(contract_id, access_token)
        
        if not items:
            return None
        
        # Appraise each item
        appraisals: list[ContractItemAppraisal] = []
        
        for item in items:
            type_id = item.get("type_id")
            quantity = item.get("quantity", 1)
            
            # Get item name from SDE
            stmt = select(InvType).where(InvType.type_id == type_id)
            result = await self.db.execute(stmt)
            inv_type = result.scalar_one_or_none()
            
            if not inv_type:
                continue
            
            # Calculate Jita Split for this item
            unit_price = await self.calculate_jita_split(type_id)
            total_value = unit_price * quantity
            
            appraisals.append(
                ContractItemAppraisal(
                    type_id=type_id,
                    name=inv_type.type_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_value=total_value
                )
            )
        
        # Calculate totals
        total_value = sum(a.total_value for a in appraisals)
        profit = total_value - asking_price
        profit_percent = (profit / asking_price * 100) if asking_price > 0 else 0
        
        # Get top 5 items by value
        top_items = sorted(appraisals, key=lambda x: x.total_value, reverse=True)[:5]
        
        return ContractAppraisal(
            contract_id=contract_id,
            total_value=total_value,
            asking_price=asking_price,
            profit=profit,
            profit_percent=profit_percent,
            item_count=len(appraisals),
            top_items=top_items
        )
    
    async def fetch_public_contracts(
        self,
        region_id: int,
        access_token: Optional[str] = None
    ) -> list[dict]:
        """
        Fetch public contracts in a region.
        
        Args:
            region_id: Region ID
            access_token: Optional OAuth access token
        
        Returns:
            List of contract dictionaries
        """
        try:
            data = await self.esi_client.get(
                f"/contracts/public/{region_id}/",
                access_token=access_token
            )
            return data
        except Exception as e:
            print(f"❌ Failed to fetch public contracts for region {region_id}: {e}")
            return []
