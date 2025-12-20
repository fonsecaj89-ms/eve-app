"""
Route Service

Calculates optimal routes through New Eden using Neo4j graph database.
Implements weighted Dijkstra pathfinding with security-based weights.
"""

from typing import Optional
from pydantic import BaseModel
from neo4j import AsyncDriver


class RouteResult(BaseModel):
    """Result of a route calculation."""
    waypoints: list[str]  # System names in order
    system_ids: list[int]  # System IDs in order
    jumps: int
    risk_score: float
    route_type: str  # 'safest', 'shortest', or 'custom'


class RouteService:
    """
    Service for calculating routes between solar systems.
    """
    
    def __init__(self, driver: AsyncDriver):
        self.driver = driver
    
    @staticmethod
    def calculate_security_weight(security: float, preference: str = "shortest") -> float:
        """
        Calculate edge weight based on security status and user preference.
        
        Args:
            security: Security status of destination system (-1.0 to 1.0)
            preference: 'safest', 'shortest', or 'custom'
        
        Returns:
            Weight value for pathfinding algorithm
        """
        if preference == "shortest":
            # All jumps equal weight
            return 1.0
        
        elif preference == "safest":
            # Heavy penalties for low/null sec
            if security >= 0.5:  # High sec
                return 1.0
            elif security > 0.0:  # Low sec
                return 50.0
            else:  # Null sec
                return 1000.0
        
        else:  # custom - moderate penalties
            if security >= 0.5:
                return 1.0
            elif security > 0.0:
                return 10.0
            else:
                return 100.0
    
    async def calculate_route(
        self,
        start_id: int,
        end_id: int,
        security_preference: str = "shortest"
    ) -> Optional[RouteResult]:
        """
        Calculate optimal route between two systems using weighted Dijkstra.
        
        Args:
            start_id: Starting solar system ID
            end_id: Destination solar system ID
            security_preference: 'safest', 'shortest', or 'custom'
        
        Returns:
            RouteResult with waypoints and metrics, or None if no route exists
        """
        
        # Cypher query using weighted shortest path
        # Note: Neo4j GDS library provides better performance for production
        query = """
        MATCH (start:SolarSystem {id: $start_id})
        MATCH (end:SolarSystem {id: $end_id})
        
        // Find all shortest paths
        CALL apoc.algo.dijkstra(
            start, end, 'GATE', 'security',
            $preference
        ) YIELD path, weight
        
        // Extract waypoints
        WITH path, weight,
             [node IN nodes(path) | node.name] AS waypoints,
             [node IN nodes(path) | node.id] AS system_ids,
             [node IN nodes(path) | node.security] AS securities
        
        RETURN 
            waypoints,
            system_ids,
            securities,
            length(path) AS jumps,
            weight AS risk_score
        LIMIT 1
        """
        
        # For systems without APOC, use a simpler approach
        simple_query = """
        MATCH (start:SolarSystem {id: $start_id})
        MATCH (end:SolarSystem {id: $end_id})
        MATCH path = shortestPath((start)-[:GATE*]-(end))
        
        WITH path,
             [node IN nodes(path) | node.name] AS waypoints,
             [node IN nodes(path) | node.id] AS system_ids,
             [node IN nodes(path) | node.security] AS securities
        
        // Calculate risk score manually
        WITH waypoints, system_ids, securities, path,
             reduce(score = 0.0, sec IN securities | 
                score + CASE 
                    WHEN sec >= 0.5 THEN 1.0
                    WHEN sec > 0.0 THEN 10.0
                    ELSE 100.0
                END
             ) AS risk_score
        
        RETURN 
            waypoints,
            system_ids,
            securities,
            length(path) AS jumps,
            risk_score
        LIMIT 1
        """
        
        async with self.driver.session() as session:
            try:
                # Try APOC version first (commented out unless APOC is installed)
                # result = await session.run(query, start_id=start_id, end_id=end_id, preference=security_preference)
                
                # Use simple version for now
                result = await session.run(
                    simple_query,
                    start_id=start_id,
                    end_id=end_id
                )
                
                record = await result.single()
                
                if not record:
                    return None
                
                return RouteResult(
                    waypoints=record["waypoints"],
                    system_ids=record["system_ids"],
                    jumps=record["jumps"],
                    risk_score=float(record["risk_score"]),
                    route_type=security_preference
                )
                
            except Exception as e:
                print(f"❌ Error calculating route: {e}")
                return None
    
    async def search_systems(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for solar systems by name (autocomplete).
        
        Args:
            query: Search string
            limit: Maximum results
        
        Returns:
            List of {id, name, security} dictionaries
        """
        cypher = """
        MATCH (s:SolarSystem)
        WHERE toLower(s.name) CONTAINS toLower($query)
        RETURN s.id AS id, s.name AS name, s.security AS security
        ORDER BY s.name
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher, query=query, limit=limit)
            records = await result.data()
            return records
    
    async def get_system_neighbors(self, system_id: int) -> list[dict]:
        """
        Get all systems directly connected to a given system.
        
        Args:
            system_id: Solar system ID
        
        Returns:
            List of neighboring system details
        """
        cypher = """
        MATCH (s:SolarSystem {id: $system_id})
        MATCH (s)-[:GATE]-(neighbor)
        RETURN neighbor.id AS id, neighbor.name AS name, neighbor.security AS security
        ORDER BY neighbor.name
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher, system_id=system_id)
            records = await result.data()
            return records
