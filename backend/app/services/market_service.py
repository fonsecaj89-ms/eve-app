"""
Market Service

Handles market data fetching and profit calculations.
Implements accurate tax and broker fee calculations using character skills.
"""

from typing import Optional
from pydantic import BaseModel
from app.clients.esi_client import ESIClient
import os


class ProfitCalculation(BaseModel):
    """Result of profit calculation."""
    buy_price: float
    sell_price: float
    gross_profit: float
    sales_tax: float
    broker_fee_buy: float
    broker_fee_sell: float
    net_profit: float
    roi: float  # Return on Investment percentage


class MarketService:
    """
    Service for market analysis and profit calculations.
    """
    
    # Base rates (can be overridden by config)
    BASE_SALES_TAX = float(os.getenv("BASE_SALES_TAX", "0.08"))  # 8%
    BASE_BROKER_FEE = float(os.getenv("BASE_BROKER_FEE", "0.03"))  # 3%
    
    def __init__(self, esi_client: ESIClient):
        self.esi_client = esi_client
    
    async def get_character_skills(self, character_id: int, access_token: str) -> dict:
        """
        Fetch character skills from ESI.
        
        Args:
            character_id: Character ID
            access_token: OAuth access token
        
        Returns:
            Dictionary with skill levels:
            {
                "accounting": int (0-5),
                "broker_relations": int (0-5)
            }
        """
        try:
            data = await self.esi_client.get(
                f"/characters/{character_id}/skills/",
                access_token=access_token
            )
            
            skills = {"accounting": 0, "broker_relations": 0}
            
            # Accounting skill ID: 16622
            # Broker Relations skill ID: 3446
            skill_map = {
                16622: "accounting",
                3446: "broker_relations"
            }
            
            for skill in data.get("skills", []):
                skill_id = skill.get("skill_id")
                if skill_id in skill_map:
                    skills[skill_map[skill_id]] = skill.get("trained_skill_level", 0)
            
            return skills
            
        except Exception as e:
            print(f"❌ Failed to fetch skills for character {character_id}: {e}")
            # Return default values
            return {"accounting": 0, "broker_relations": 0}
    
    def calculate_net_profit(
        self,
        buy_price: float,
        sell_price: float,
        accounting_level: int = 0,
        broker_relations_level: int = 0,
        standings: float = 0.0
    ) -> ProfitCalculation:
        """
        Calculate net profit with accurate tax and broker fee calculations.
        
        Formula:
        - Sales Tax = Base (8%) reduced by 11% per Accounting level
        - Broker Fee = Base (3%) reduced by 0.3% per Broker Relations level
          and further reduced by standings
        
        Args:
            buy_price: Price to buy the item
            sell_price: Price to sell the item
            accounting_level: Accounting skill level (0-5)
            broker_relations_level: Broker Relations skill level (0-5)
            standings: Character standings with corporation (0.0 to 10.0)
        
        Returns:
            ProfitCalculation with detailed breakdown
        """
        # Calculate effective sales tax
        # Base 8%, reduced by 11% per level
        # Formula: 8% * (1 - 0.11 * accounting_level)
        effective_tax_rate = self.BASE_SALES_TAX * (1 - 0.11 * accounting_level)
        sales_tax = sell_price * effective_tax_rate
        
        # Calculate effective broker fee
        # Base 3%, reduced by 0.3% per level and by standings
        # Formula: (3% - 0.3% * broker_level) * (1 - 0.03 * standings)
        base_broker = self.BASE_BROKER_FEE - (0.003 * broker_relations_level)
        effective_broker_rate = base_broker * (1 - 0.03 * standings)
        
        # Broker fees apply to both buy and sell orders
        broker_fee_buy = buy_price * effective_broker_rate
        broker_fee_sell = sell_price * effective_broker_rate
        
        # Calculate profits
        gross_profit = sell_price - buy_price
        net_profit = gross_profit - sales_tax - broker_fee_buy - broker_fee_sell
        
        # ROI = (net_profit / total_invested) * 100
        total_invested = buy_price + broker_fee_buy
        roi = (net_profit / total_invested * 100) if total_invested > 0 else 0
        
        return ProfitCalculation(
            buy_price=buy_price,
            sell_price=sell_price,
            gross_profit=gross_profit,
            sales_tax=sales_tax,
            broker_fee_buy=broker_fee_buy,
            broker_fee_sell=broker_fee_sell,
            net_profit=net_profit,
            roi=roi
        )
    
    async def fetch_market_orders(
        self,
        region_id: int,
        type_id: Optional[int] = None,
        order_type: Optional[str] = None
    ) -> list[dict]:
        """
        Fetch market orders from ESI with pagination support.
        
        Args:
            region_id: Region ID
            type_id: Optional item type ID filter
            order_type: Optional 'buy' or 'sell' filter
        
        Returns:
            List of market order dictionaries
        """
        endpoint = f"/markets/{region_id}/orders/"
        params = {}
        
        if type_id:
            params["type_id"] = type_id
        if order_type:
            params["order_type"] = order_type
        
        try:
            # Fetch first page to check for pagination
            data = await self.esi_client.get(endpoint, params=params)
            
            # ESI returns list directly for market orders
            # Filter orders with at least 1 day remaining
            filtered_orders = [
                order for order in data
                if order.get("duration", 0) >= 1
            ]
            
            return filtered_orders
            
        except Exception as e:
            print(f"❌ Failed to fetch market orders for region {region_id}: {e}")
            return []
    
    async def calculate_arbitrage(
        self,
        region_a: int,
        region_b: int,
        min_volume: int = 1000,
        min_profit_percent: float = 5.0
    ) -> list[dict]:
        """
        Calculate arbitrage opportunities between two regions.
        
        Logic: Find items where region_b buy price > region_a sell price
        
        Args:
            region_a: Source region ID
            region_b: Destination region ID
            min_volume: Minimum order volume to consider
            min_profit_percent: Minimum profit percentage threshold
        
        Returns:
            List of arbitrage opportunities sorted by profit descending
        """
        # This is a simplified version - full implementation would:
        # 1. Fetch all orders for both regions
        # 2. Group by type_id
        # 3. Find best buy/sell matches
        # 4. Calculate profit with skills
        # 5. Sort by profit
        
        # For now, return empty list (to be implemented with full market cache)
        return []
    
    async def get_best_prices(
        self,
        region_id: int,
        type_id: int
    ) -> dict:
        """
        Get best buy and sell prices for an item in a region.
        
        Args:
            region_id: Region ID
            type_id: Item type ID
        
        Returns:
            {
                "best_buy": float or None,
                "best_sell": float or None,
                "buy_volume": int,
                "sell_volume": int
            }
        """
        orders = await self.fetch_market_orders(region_id, type_id=type_id)
        
        buy_orders = [o for o in orders if o.get("is_buy_order")]
        sell_orders = [o for o in orders if not o.get("is_buy_order")]
        
        best_buy = max([o.get("price", 0) for o in buy_orders], default=None)
        best_sell = min([o.get("price", float('inf')) for o in sell_orders], default=None)
        
        buy_volume = sum([o.get("volume_remain", 0) for o in buy_orders])
        sell_volume = sum([o.get("volume_remain", 0) for o in sell_orders])
        
        return {
            "best_buy": best_buy,
            "best_sell": best_sell if best_sell != float('inf') else None,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume
        }
