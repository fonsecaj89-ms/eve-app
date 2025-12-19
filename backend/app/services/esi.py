import asyncio
import time
import httpx
from typing import Optional, Any, Dict
from app.db.redis import get_redis_client
from app.logger import structlog

logger = structlog.get_logger()

ESI_BASE_URL = "https://esi.evetech.net/latest"
LOCKDOWN_KEY = "ESI_GLOBAL_LOCKDOWN"

class EsiClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        
    async def _check_lockdown(self):
        r = get_redis_client()
        if await r.exists(LOCKDOWN_KEY):
            logger.error("esi_lockdown_active", msg="Request blocked due to global lockdown.")
            raise Exception("429 Too Many Requests: ESI Global Lockdown Active")

    async def _trigger_lockdown(self, reason: str):
        logger.critical("esi_trigger_lockdown", reason=reason)
        r = get_redis_client()
        await r.setex(LOCKDOWN_KEY, 60, "1") # 1 minute lockdown
        await asyncio.sleep(30) # Sleep 30s immediately

    async def request_raw(self, method: str, endpoint: str, params: Optional[Dict] = None) -> httpx.Response:
        """
        Returns full httpx response for header inspection.
        """
        await self._check_lockdown()
        
        url = f"{ESI_BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            response = await self.client.request(method, url, params=params)
            process_time = time.time() - start_time
            
            # Rate Limit Headers
            limit_remain = response.headers.get("x-esi-error-limit-remain")
            
            logger.info(
                "esi_request", 
                method=method, 
                url=url, 
                status=response.status_code, 
                limit_remain=limit_remain
            )
            
            if response.status_code >= 400:
                logger.error("esi_error", status=response.status_code, body=response.text)
                if response.status_code != 404:
                    await self._trigger_lockdown(f"Status {response.status_code}")
                    raise Exception(f"ESI Error {response.status_code}")

            return response

        except httpx.RequestError as e:
            logger.error("esi_connection_error", error=str(e))
            raise e

    async def get_all_pages(self, endpoint: str, params: Optional[Dict] = None) -> list:
        """
        Handles X-Pages pagination with 2s delay.
        """
        if params is None:
            params = {}
            
        all_results = []
        
        # First page
        response = await self.request_raw("GET", endpoint, params=params)
        all_results.extend(response.json())
        
        TOTAL_PAGES = int(response.headers.get("X-Pages", 1))
        
        if TOTAL_PAGES > 1:
            for page in range(2, TOTAL_PAGES + 1):
                params["page"] = page
                await asyncio.sleep(2.0) # 2-second delay as requested
                
                resp = await self.request_raw("GET", endpoint, params=params)
                all_results.extend(resp.json())
                
        return all_results

    async def request(self, method: str, endpoint: str, params: Optional[Dict] = None, retry: int = 0) -> Any:
        response = await self.request_raw(method, endpoint, params)
        return response.json()

    async def close(self):
        await self.client.aclose()

# Singleton instance
esi_client = EsiClient()
