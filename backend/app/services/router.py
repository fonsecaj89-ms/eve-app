import asyncio
from app.db.neo4j import get_neo4j_driver
from app.services.esi import esi_client
from app.logger import structlog

logger = structlog.get_logger()

class RouterService:
    async def update_safety_data(self):
        """
        Fetches /universe/system_kills/ and updates Edge weights in Neo4j.
        """
        logger.info("routing_safety_update_start")
        try:
            # Fetch kills from ESI
            kills = await esi_client.request("GET", "/universe/system_kills/")
            
            # Identify dangerous systems
            # Logic: If pod_kills > 0 or ship_kills > 5 in last hour?
            # Prompt: "Smartbomb Avoidance: If a system has high kills... increase edge weight significantly."
            
            dangerous_systems = []
            for k in kills:
                if k.get("pod_kills", 0) > 0 or k.get("ship_kills", 0) > 5:
                    dangerous_systems.append(k["system_id"])
            
            if not dangerous_systems:
                logger.info("routing_safety_update_clean", msg="No dangerous systems found.")
                return

            # Update Neo4j
            driver = get_neo4j_driver()
            with driver.session() as session:
                # 1. Reset all weights to 1.0 (base) first? 
                # This might be slow. Optimization: Only update dangerous ones and strict reset others periodically?
                # Or we assume default query uses property 'weight' and we only SET it for dangerous ones.
                # If we rely on persistence, we must reset old dangerous ones.
                # Brute force reset for now:
                
                reset_query = """
                MATCH ()-[r:GATE]->()
                SET r.weight = 1.0
                """
                session.run(reset_query)
                
                # 2. Set High Weight for Dangerous
                update_query = """
                UNWIND $ids as sys_id
                MATCH (s:System {id: sys_id})-[r:GATE]-() -- Both incoming and outgoing? Or just entering?
                -- "GATE" is usually bidirectional in connectivity but modeled as directed?
                -- If we want to avoid TRANSITING, we penalize edges connected to it.
                SET r.weight = 1000.0
                """
                session.run(update_query, ids=dangerous_systems)
                
            logger.info("routing_safety_update_complete", dangerous_count=len(dangerous_systems))
            
        except Exception as e:
            logger.error("routing_safety_update_error", error=str(e))

    async def get_route(self, origin: int, destination: int, avoid_unsafe: bool = True):
        """
        Calculate route using Dijkstra/A* in Neo4j.
        """
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Use APOC Dijkstra
            # weight property is 'weight' (1.0 or 1000.0)
            
            query = """
            MATCH (start:System {id: $origin}), (end:System {id: $destination})
            CALL apoc.algo.dijkstra(start, end, 'GATE', 'weight') YIELD path, weight
            RETURN [n in nodes(path) | n.id] as system_ids, weight
            """
            
            # If APOC not available, we can use built-in shortestPath but that doesn't support weights easily without GDS.
            # Assuming APOC is installed (Prompt mentioned enabling it).
            
            result = session.run(query, origin=origin, destination=destination).single()
            
            if result:
                return {
                    "path": result["system_ids"],
                    "total_cost": result["weight"]
                }
            return None

router_service = RouterService()
