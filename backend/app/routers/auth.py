"""
Authentication Router

Handles EVE SSO OAuth2 flow:
- /auth/login: Redirects to EVE SSO
- /auth/callback: Handles OAuth callback (CRITICAL - proxied from frontend)
- /auth/logout: Clears session
- /auth/session: Gets current session info
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
import os
from urllib.parse import urlencode
import secrets
import json
import logging
import traceback

# Setup logger
logger = logging.getLogger("uvicorn.error")

from app.cache import get_redis
from app.clients.token_manager import TokenManager


router = APIRouter()

# EVE SSO configuration
EVE_CLIENT_ID = os.getenv("EVE_CLIENT_ID")
EVE_CALLBACK_URL = os.getenv("EVE_CALLBACK_URL", "https://eve-app.jf-nas.com/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://eve-app.jf-nas.com")

# EVE SSO scopes
EVE_SCOPES = os.getenv("EVE_SCOPES", "").split()
if not EVE_SCOPES:
    EVE_SCOPES = [
        "esi-wallet.read_character_wallet.v1",
        "esi-skills.read_skills.v1",
        "esi-markets.read_character_orders.v1",
        "esi-characters.read_blueprints.v1",
        "esi-industry.read_character_jobs.v1",
        "esi-contracts.read_character_contracts.v1",
        "esi-assets.read_assets.v1",
        "esi-universe.read_structures.v1",
        "esi-search.search_structures.v1"
    ]


@router.get("/login")
async def login():
    """
    Redirect to EVE SSO for authentication.
    
    Flow:
    1. User clicks login
    2. Redirect to EVE SSO with scopes
    3. User authorizes
    4. EVE redirects to callback URL
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    logger.info(f"➡️ Initiating login. State: {state[:10]}...")
    
    # Build EVE SSO authorization URL
    params = {
        "response_type": "code",
        "redirect_uri": EVE_CALLBACK_URL,
        "client_id": EVE_CLIENT_ID,
        "scope": " ".join(EVE_SCOPES),
        "state": state
    }
    
    auth_url = f"https://login.eveonline.com/v2/oauth/authorize/?{urlencode(params)}"
    
    # Store state in session cookie for verification
    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=300  # 5 minutes
    )
    
    return response


@router.get("/callback")
async def callback(
    code: str,
    state: str,
    request: Request,
    redis: Redis = Depends(get_redis)
):
    """
    Handle OAuth callback from EVE SSO.
    
    CRITICAL: This endpoint is called via Vite proxy:
    EVE SSO → https://eve-app.jf-nas.com/callback 
           → Cloudflare Tunnel 
           → Vite Frontend 
           → Proxy to backend /auth/callback
    
    This is where tokens are stored in Redis.
    """
    logger.info(f"⬅️ Callback received. Code len: {len(code)}, State: {state[:10]}...")
    
    # Verify state (CSRF protection)
    stored_state = request.cookies.get("oauth_state")
    if not stored_state:
        logger.error("❌ No stored state cookie found")
        raise HTTPException(status_code=400, detail="Invalid state parameter (missing cookie)")
        
    if stored_state != state:
        logger.error(f"❌ State mismatch. Received: {state}, Stored: {stored_state}")
        raise HTTPException(status_code=400, detail="Invalid state parameter (mismatch)")
    
    # Exchange code for tokens
    token_manager = TokenManager(redis)
    
    try:
        logger.info("🔄 Exchanging code for tokens...")
        character_info, access_token, refresh_token, expires_in = \
            await token_manager.exchange_code_for_tokens(code)
        
        character_id = character_info.get("CharacterID")
        character_name = character_info.get("CharacterName")
        
        # Store tokens in Redis
        await token_manager.store_tokens(
            character_id,
            access_token,
            refresh_token,
            expires_in
        )
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "character_id": character_id,
            "character_name": character_name,
            "character_owner_hash": character_info.get("CharacterOwnerHash")
        }
        
        logger.info(f"💾 Storing session for {character_name} ({character_id})")
        
        # Store session in Redis (30 day expiry)
        await redis.setex(
            f"session:{session_id}",
            30 * 24 * 60 * 60,  # 30 days
            json.dumps(session_data)
        )
        
        # Redirect to frontend dashboard with session cookie
        logger.info("➡️ Redirecting to dashboard")
        response = RedirectResponse(url=f"{FRONTEND_URL}/dashboard")
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        # Clear oauth_state cookie
        response.delete_cookie("oauth_state")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ OAuth callback failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis)
):
    """
    Logout current user and clear session.
    """
    session_id = request.cookies.get("session_id")
    
    if session_id:
        # Delete session from Redis
        await redis.delete(f"session:{session_id}")
    
    # Clear session cookie
    response.delete_cookie("session_id")
    
    return {"message": "Logged out successfully"}


@router.get("/session")
async def get_session(
    request: Request,
    redis: Redis = Depends(get_redis)
):
    """
    Get current session information.
    
    Returns:
        {
            "character_id": int,
            "character_name": str,
            "authenticated": bool
        }
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        return {"authenticated": False}
    
    # Get session from Redis
    session_data = await redis.get(f"session:{session_id}")
    
    if not session_data:
        return {"authenticated": False}
    
    # Parse session data (stored as JSON)
    session = json.loads(session_data)
    
    return {
        "authenticated": True,
        "character_id": session.get("character_id"),
        "character_name": session.get("character_name")
    }
