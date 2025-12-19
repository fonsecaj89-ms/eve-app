import os
import subprocess
import time
from pathlib import Path
from sqlmodel import Session, select, text
from app.db.engine import engine
from app.db.neo4j import get_neo4j_driver
from app.models.sde import MapSolarSystem, MapSolarSystemJumps
from app.logger import structlog

logger = structlog.get_logger()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
EVE_DATA_DIR = BASE_DIR / "eve_data"
DUMP_FILE = EVE_DATA_DIR / "postgres-latest.dmp"

def restore_postgres():
    """
    Restores the Fuzzwork SDE dump into the Postgres container.
    """
    if not DUMP_FILE.exists():
        logger.error("ingestion_failed", error="Dump file not found", path=str(DUMP_FILE))
        return

    logger.info("ingestion_started", stage="postgres_restore")
    
    # Command to pipe dump to docker container
    # Assuming 'eve-postgres' is the container name or 'postgres' service in compose
    # Using docker-compose exec -T for non-interactive
    
    cmd = [
        "docker-compose", "exec", "-T", "postgres",
        "pg_restore", "-U", "eve_admin", "-d", "eve_db",
        "--clean", "--if-exists", "--no-owner", "--no-privileges"
    ]

    try:
        with open(DUMP_FILE, "rb") as f:
            process = subprocess.Popen(
                cmd, 
                stdin=f, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=str(BASE_DIR) # Run from root where docker-compose.yml is
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0 and process.returncode != 1: # pg_restore returns 1 on warnings
                 # Check if stderr contains actual errors
                 logger.error("ingestion_failed", stage="postgres_restore", stderr=stderr.decode())
                 # Continuing might be risky, but Fuzzwork dump often has minor warnings
            else:
                 logger.info("ingestion_success", stage="postgres_restore")

    except Exception as e:
        logger.error("ingestion_exception", error=str(e))

def build_neo4j_graph():
    """
    Reads SDE data from Postgres and populates Neo4j.
    """
    logger.info("ingestion_started", stage="neo4j_graph_build")
    driver = get_neo4j_driver()
    
    with Session(engine) as postgres_session:
        # Fetch Systems
        logger.info("fetching_systems")
        systems = postgres_session.exec(select(MapSolarSystem)).all()
        
        # Batch Create System Nodes
        driver = get_neo4j_driver()
        with driver.session() as neo_session:
            # Create Constraints
            neo_session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:System) REQUIRE s.id IS UNIQUE")
            
            logger.info("creating_nodes", count=len(systems))
            # Batch query for nodes
            query = """
            UNWIND $batch AS row
            MERGE (s:System {id: row.id})
            SET s.name = row.name, s.security = row.security
            """
            
            # Helper for batching
            batch_size = 1000
            batch = []
            for s in systems:
                batch.append({
                    "id": s.solarSystemID,
                    "name": s.solarSystemName,
                    "security": s.security
                })
                if len(batch) >= batch_size:
                    neo_session.run(query, batch=batch)
                    batch = []
            if batch:
                neo_session.run(query, batch=batch)

        # Fetch Jumps
        logger.info("fetching_jumps")
        # Direct raw SQL might be faster or safer if SQLModel mapping is partial
        # But we have MapSolarSystemJumps
        jumps = postgres_session.exec(select(MapSolarSystemJumps)).all()
        
        with driver.session() as neo_session:
            logger.info("creating_edges", count=len(jumps))
            query = """
            UNWIND $batch AS row
            MATCH (a:System {id: row.from})
            MATCH (b:System {id: row.to})
            MERGE (a)-[r:GATE]->(b)
            SET r.weight = 1.0 // Base weight, modified by routing engine later
            """
            
            batch = []
            for j in jumps:
                batch.append({
                    "from": j.fromSolarSystemID,
                    "to": j.toSolarSystemID
                })
                if len(batch) >= batch_size:
                    neo_session.run(query, batch=batch)
                    batch = []
            if batch:
                neo_session.run(query, batch=batch)
            
    logger.info("ingestion_success", stage="neo4j_graph_build")

if __name__ == "__main__":
    restore_postgres()
    # Wait a bit for DB to settle? Usually not needed if restore finished.
    # We must ensure Postgres is ready for Querying
    time.sleep(5)
    build_neo4j_graph()
