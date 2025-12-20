"""
FastAPI Main Application

EVE Online Trading Platform - Backend API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import init_db, close_db
from app.graph import get_neo4j_driver, close_neo4j
from app.cache import get_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events - startup and shutdown.
    """
    # Startup
    print("🚀 Starting EVE Online Trading Platform API...")
    
    await init_db()
    print("✅ Database connection established")
    
    await get_neo4j_driver()
    print("✅ Neo4j connection established")
    
    await get_redis()
    print("✅ Redis connection established")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down API...")
    await close_db()
    await close_neo4j()
    await close_redis()
    print("✅ All connections closed")


# Create FastAPI application
app = FastAPI(
    title="EVE Online Trading Platform API",
    description="""
    High-frequency trading and industry analytics platform for EVE Online.
    
    ## Features
    
    * **Market Analysis**: Real-time arbitrage detection and profit calculations
    * **Route Planning**: Security-weighted graph pathfinding via Neo4j
    * **Contract Appraisal**: Jita Split methodology for accurate valuations
    * **ESI Compliance**: Strict rate limiting with error budget management
    * **Character Integration**: Wallet tracking, skills, and transaction history
    
    ## Authentication
    
    Uses EVE Online SSO OAuth2 flow. Access `/auth/login` to start authentication.
    
    ## Rate Limiting
    
    All ESI requests are subject to strict rate limiting to ensure API compliance.
    The system implements error budget management with three states:
    - Green (< 50 errors): Normal operation
    - Yellow (50-90 errors): Exponential backoff
    - Red (≥ 90 errors): Lockdown mode
    
    ## Data Sources
    
    - **SDE**: Fuzzwork PostgreSQL dump for static EVE data
    - **ESI**: EVE Swagger Interface for real-time game data
    - **Neo4j**: Graph database for route planning
    - **Redis**: Caching and session management
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "EVE SSO OAuth2 authentication flow"
        },
        {
            "name": "Market",
            "description": "Market data, orders, prices, and arbitrage analysis"
        },
        {
            "name": "Contracts",
            "description": "Contract fetching and Jita Split appraisal"
        },
        {
            "name": "Character",
            "description": "Character-specific data (requires authentication)"
        },
        {
            "name": "Universe",
            "description": "Search for items, systems, stations, and regions"
        },
        {
            "name": "Routing",
            "description": "Route calculation with security-weighted pathfinding"
        },
        {
            "name": "Health",
            "description": "Service health and status checks"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://eve-app.jf-nas.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
from app.routers import auth, market, contracts, character, universe, routing

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(market.router, prefix="/market", tags=["Market"])
app.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
app.include_router(character.router, prefix="/character", tags=["Character"])
app.include_router(universe.router, prefix="/universe", tags=["Universe"])
app.include_router(routing.router, prefix="/routing", tags=["Routing"])


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for Docker healthcheck and monitoring.
    
    Returns:
        {
            "status": "healthy",
            "service": "eve-trading-platform",
            "environment": str
        }
    """
    return {
        "status": "healthy",
        "service": "eve-trading-platform",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint with API information and links.
    
    Returns basic API metadata and navigation links.
    """
    return {
        "message": "EVE Online Trading Platform API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "health": "/health",
        "endpoints": {
            "auth": "/auth",
            "market": "/market",
            "contracts": "/contracts",
            "character": "/character", 
            "universe": "/universe",
            "routing": "/routing"
        }
    }
