"""
Neo4j Graph Database Connection

Provides async Neo4j driver for route planning and topology queries.
"""

from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import AsyncGenerator
import os


# Neo4j connection configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Global driver instance
_driver: AsyncDriver | None = None


async def get_neo4j_driver() -> AsyncDriver:
    """
    Get or create the Neo4j driver instance.
    """
    global _driver
    
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_pool_size=50,
            connection_acquisition_timeout=60.0,
        )
        
        # Verify connectivity
        await _driver.verify_connectivity()
        print(f"✅ Neo4j connected: {NEO4J_URI}")
    
    return _driver


async def get_graph():
    """
    FastAPI dependency for Neo4j sessions.
    
    Usage:
        @app.get("/route/")
        async def calculate_route(driver: AsyncDriver = Depends(get_graph)):
            async with driver.session() as session:
                ...
    """
    driver = await get_neo4j_driver()
    return driver


async def close_neo4j():
    """
    Close Neo4j driver on application shutdown.
    """
    global _driver
    
    if _driver is not None:
        await _driver.close()
        print("✅ Neo4j connections closed")
        _driver = None
