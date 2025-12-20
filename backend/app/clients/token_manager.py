"""
OAuth Token Manager

Manages EVE SSO OAuth tokens lifecycle:
- Stores access/refresh tokens in Redis
- Automatically refreshes tokens before expiration
- Thread-safe token retrieval
"""

import httpx
from typing import Optional, Tuple
from datetime import datetime, timedelta
from redis.asyncio import Redis
import json
import os


class TokenManager:
    """
    Manages OAuth token lifecycle for EVE SSO.
    """
    
    # EVE SSO endpoints
    SSO_TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
    SSO_VERIFY_URL = "https://login.eveonline.com/oauth/verify"
    
    # Redis key patterns
    KEY_ACCESS_TOKEN = "token:{character_id}:access"
    KEY_REFRESH_TOKEN = "token:{character_id}:refresh"
    KEY_TOKEN_EXPIRY = "token:{character_id}:expiry"
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.client_id = os.getenv("EVE_CLIENT_ID")
        self.client_secret = os.getenv("EVE_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("EVE_CLIENT_ID and EVE_CLIENT_SECRET must be set")
    
    async def store_tokens(
        self,
        character_id: int,
        access_token: str,
        refresh_token: str,
        expires_in: int
    ):
        """
        Store OAuth tokens in Redis.
        
        Args:
            character_id: EVE character ID
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Seconds until access token expires
        """
        expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Store tokens with character_id as key
        await self.redis.setex(
            self.KEY_ACCESS_TOKEN.format(character_id=character_id),
            expires_in,
            access_token
        )
        
        await self.redis.set(
            self.KEY_REFRESH_TOKEN.format(character_id=character_id),
            refresh_token
        )
        
        await self.redis.set(
            self.KEY_TOKEN_EXPIRY.format(character_id=character_id),
            expiry_time.isoformat()
        )
        
        print(f"✅ Stored tokens for character {character_id}")
    
    async def get_access_token(self, character_id: int) -> Optional[str]:
        """
        Get valid access token for character, refreshing if needed.
        
        Args:
            character_id: EVE character ID
        
        Returns:
            Valid access token or None if not found
        """
        # Check if token exists and is valid
        access_token = await self.redis.get(
            self.KEY_ACCESS_TOKEN.format(character_id=character_id)
        )
        
        if access_token:
            # Check expiry
            expiry_str = await self.redis.get(
                self.KEY_TOKEN_EXPIRY.format(character_id=character_id)
            )
            
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str)
                # Refresh if less than 5 minutes remaining
                if datetime.utcnow() + timedelta(minutes=5) >= expiry:
                    print(f"🔄 Token expiring soon for character {character_id}, refreshing...")
                    return await self._refresh_token(character_id)
            
            return access_token
        
        # Try to refresh
        return await self._refresh_token(character_id)
    
    async def _refresh_token(self, character_id: int) -> Optional[str]:
        """
        Refresh access token using refresh token.
        
        Args:
            character_id: EVE character ID
        
        Returns:
            New access token or None if refresh failed
        """
        refresh_token = await self.redis.get(
            self.KEY_REFRESH_TOKEN.format(character_id=character_id)
        )
        
        if not refresh_token:
            print(f"❌ No refresh token found for character {character_id}")
            return None
        
        # Request new tokens
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.SSO_TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token
                    },
                    auth=(self.client_id, self.client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                # Store new tokens
                await self.store_tokens(
                    character_id,
                    token_data["access_token"],
                    token_data.get("refresh_token", refresh_token),  # Some responses don't include new refresh token
                    token_data["expires_in"]
                )
                
                return token_data["access_token"]
                
            except httpx.HTTPError as e:
                print(f"❌ Token refresh failed for character {character_id}: {e}")
                return None
    
    async def exchange_code_for_tokens(self, code: str) -> Tuple[dict, str, str, int]:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from OAuth callback
        
        Returns:
            Tuple of (character_info, access_token, refresh_token, expires_in)
        
        Raises:
            httpx.HTTPError: If token exchange fails
        """
        async with httpx.AsyncClient() as client:
            # Exchange code for tokens
            response = await client.post(
                self.SSO_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code
                },
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            access_token = token_data["access_token"]
            refresh_token = token_data["refresh_token"]
            expires_in = token_data["expires_in"]
            
            # Verify token and get character info
            verify_response = await client.get(
                self.SSO_VERIFY_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            verify_response.raise_for_status()
            character_info = verify_response.json()
            
            return character_info, access_token, refresh_token, expires_in
    
    async def revoke_tokens(self, character_id: int):
        """
        Revoke and delete tokens for a character.
        
        Args:
            character_id: EVE character ID
        """
        # Delete from Redis
        await self.redis.delete(
            self.KEY_ACCESS_TOKEN.format(character_id=character_id)
        )
        await self.redis.delete(
            self.KEY_REFRESH_TOKEN.format(character_id=character_id)
        )
        await self.redis.delete(
            self.KEY_TOKEN_EXPIRY.format(character_id=character_id)
        )
        
        print(f"✅ Revoked tokens for character {character_id}")
