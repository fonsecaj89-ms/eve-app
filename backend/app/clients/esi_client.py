"""
ESI Client with Strict Compliance

Implements error budget management, HTTP 420 lockdown, and cache-aware requests
to ensure compliance with EVE ESI API requirements.

ESI Error Budget:
- Green (< 50 errors): Normal operation
- Yellow (50-90 errors): Exponential backoff + jitter
- Red (≥ 90 errors): Lockdown, all requests blocked

HTTP 420 Response: Global lockdown until error window expires
"""

import httpx
import asyncio
import random
from typing import Optional, Any
from datetime import datetime, timedelta
from redis.asyncio import Redis
import json


class ESILockdownException(Exception):
    """Raised when ESI is in lockdown mode due to error budget exhaustion."""
    pass


class ESIClient:
    """
    ESI HTTP client with strict compliance mechanisms.
    """
    
    BASE_URL = "https://esi.evetech.net/latest"
    USER_AGENT = "EVE-Trading-Platform/1.0 (https://github.com/yourusername/eve-app)"
    
    # Error budget thresholds
    ERROR_THRESHOLD_YELLOW = 50
    ERROR_THRESHOLD_RED = 90
    
    # Redis keys
    KEY_ERROR_COUNT = "esi:error_count"
    KEY_ERROR_RESET = "esi:error_reset"
    KEY_GLOBAL_LOCK = "esi:global_lock"
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            headers={"User-Agent": self.USER_AGENT}
        )
    
    async def _check_global_lock(self):
        """
        Check if ESI is in global lockdown (HTTP 420 received).
        Raises ESILockdownException if locked.
        """
        lock_until = await self.redis.get(self.KEY_GLOBAL_LOCK)
        if lock_until:
            lock_time = datetime.fromisoformat(lock_until)
            if datetime.utcnow() < lock_time:
                remaining = (lock_time - datetime.utcnow()).total_seconds()
                raise ESILockdownException(
                    f"ESI in global lockdown due to HTTP 420. "
                    f"Retry after {remaining:.0f} seconds"
                )
            else:
                # Lock expired, remove it
                await self.redis.delete(self.KEY_GLOBAL_LOCK)
    
    async def _get_error_budget(self) -> dict:
        """
        Get current error budget status from Redis.
        
        Returns:
            {
                "error_count": int,
                "reset_time": datetime or None,
                "status": "green" | "yellow" | "red"
            }
        """
        error_count = await self.redis.get(self.KEY_ERROR_COUNT)
        error_count = int(error_count) if error_count else 0
        
        reset_time_str = await self.redis.get(self.KEY_ERROR_RESET)
        reset_time = datetime.fromisoformat(reset_time_str) if reset_time_str else None
        
        # Determine status
        if error_count < self.ERROR_THRESHOLD_YELLOW:
            status = "green"
        elif error_count < self.ERROR_THRESHOLD_RED:
            status = "yellow"
        else:
            status = "red"
        
        return {
            "error_count": error_count,
            "reset_time": reset_time,
            "status": status
        }
    
    async def _update_error_budget(self, headers: dict):
        """
        Update error budget based on ESI response headers.
        
        Headers:
            X-ESI-Error-Limit-Remain: Errors remaining in window
            X-ESI-Error-Limit-Reset: Seconds until window reset
        """
        remain = headers.get("X-ESI-Error-Limit-Remain")
        reset = headers.get("X-ESI-Error-Limit-Reset")
        
        if remain is not None:
            error_count = 100 - int(remain)
            await self.redis.set(self.KEY_ERROR_COUNT, error_count)
            
            if reset is not None:
                reset_time = datetime.utcnow() + timedelta(seconds=int(reset))
                await self.redis.set(
                    self.KEY_ERROR_RESET,
                    reset_time.isoformat()
                )
    
    async def _apply_backoff(self, status: str):
        """
        Apply backoff delay based on error budget status.
        """
        if status == "yellow":
            # Exponential backoff with jitter (500ms - 2s)
            delay = random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
        elif status == "red":
            # Heavy backoff (2s - 5s)
            delay = random.uniform(2.0, 5.0)
            await asyncio.sleep(delay)
    
    async def _get_cached_response(self, cache_key: str) -> Optional[dict]:
        """
        Get cached ESI response if available.
        """
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    async def _cache_response(self, cache_key: str, data: Any, ttl: int):
        """
        Cache ESI response with TTL from Expires header.
        """
        await self.redis.setex(cache_key, ttl, json.dumps(data))
    
    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        access_token: Optional[str] = None,
        use_cache: bool = True
    ) -> dict:
        """
        Execute GET request to ESI with full compliance checks.
        
        Args:
            endpoint: ESI endpoint (e.g., "/markets/10000002/orders/")
            params: Query parameters
            access_token: OAuth access token for authenticated endpoints
            use_cache: Whether to use cached responses
        
        Returns:
            Response data as dictionary
        
        Raises:
            ESILockdownException: If in lockdown mode
            httpx.HTTPError: For other HTTP errors
        """
        # Check global lockdown
        await self._check_global_lock()
        
        # Check error budget
        budget = await self._get_error_budget()
        
        if budget["status"] == "red":
            raise ESILockdownException(
                f"ESI error budget exhausted ({budget['error_count']}/100 errors). "
                f"Requests blocked until reset."
            )
        
        # Apply backoff if needed
        await self._apply_backoff(budget["status"])
        
        # Check cache
        cache_key = f"esi:cache:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        if use_cache:
            cached = await self._get_cached_response(cache_key)
            if cached:
                return cached
        
        # Build request
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        # Execute request
        try:
            response = await self.http_client.get(url, params=params, headers=headers)
            
            # Update error budget from headers
            await self._update_error_budget(response.headers)
            
            # Handle HTTP 420 - Error Limited
            if response.status_code == 420:
                retry_after = int(response.headers.get("Retry-After", 300))
                lock_until = datetime.utcnow() + timedelta(seconds=retry_after)
                await self.redis.set(self.KEY_GLOBAL_LOCK, lock_until.isoformat())
                
                raise ESILockdownException(
                    f"ESI returned HTTP 420. Locked for {retry_after} seconds."
                )
            
            # Raise for other errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Cache response if Expires header present
            if "Expires" in response.headers and use_cache:
                expires = response.headers["Expires"]
                # Parse expires and calculate TTL
                # Simplified: cache for 5 minutes by default
                ttl = 300
                await self._cache_response(cache_key, data, ttl)
            
            return data
            
        except httpx.HTTPStatusError as e:
            print(f"❌ ESI HTTP error: {e.response.status_code} - {endpoint}")
            raise
        except httpx.RequestError as e:
            print(f"❌ ESI request error: {e} - {endpoint}")
            raise
    
    async def close(self):
        """
        Close HTTP client.
        """
        await self.http_client.aclose()
