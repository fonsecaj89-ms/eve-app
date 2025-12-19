import json
from app.db.redis import get_redis_client
from app.services.esi import esi_client
from app.services.market import market_service
from app.logger import structlog

logger = structlog.get_logger()
JITA_REGION_ID = 10000002

class ContractService:
    async def fetch_public_contracts(self, region_id: int = JITA_REGION_ID):
        """
        Fetches public contracts and caches them in Redis.
        """
        # ESI endpoint: /contracts/public/{region_id}/
        endpoint = f"/contracts/public/{region_id}/"
        
        # This can be many pages.
        contracts = await esi_client.get_all_pages(endpoint)
        
        r = get_redis_client()
        pipe = r.pipeline()
        
        count = 0
        for c in contracts:
            if c["type"] == "item_exchange": # Start with Item Exchange only
                key = f"contract:{c['contract_id']}"
                # Cache for 30 days or until expiration?
                # Using 30 days as requested.
                pipe.setex(key, 30 * 24 * 3600, json.dumps(c))
                count += 1
        
        await pipe.execute()
        logger.info("contracts_cached", region_id=region_id, count=count)
        return contracts

    async def value_contract(self, contract_id: int):
        """
        Valuate a contract by checking its items against Jita Sell Price.
        """
        # 1. Fetch Items for Contract
        # /contracts/public/items/{contract_id}/
        # WARNING: This endpoint is often paged too but usually small for single contract.
        
        endpoint = f"/contracts/public/items/{contract_id}/"
        items = await esi_client.get_all_pages(endpoint)
        
        total_valuation = 0.0
        details = []
        
        for item in items:
            type_id = item["type_id"]
            qty = item["quantity"]
            
            # Get Jita Price
            price = await market_service.get_min_sell_price(JITA_REGION_ID, type_id)
            if price == 0:
                # Fallback or flag unknown?
                pass
            
            item_val = price * qty
            total_valuation += item_val
            details.append({
                "type_id": type_id,
                "qty": qty,
                "unit_price": price,
                "total": item_val
            })
            
        return {
            "contract_id": contract_id,
            "valuation": total_valuation,
            "items": details
        }

contract_service = ContractService()
