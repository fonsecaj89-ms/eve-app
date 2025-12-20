"""
Neo4j Graph Build Script

ETL Pipeline: PostgreSQL SDE → Neo4j Topology Graph

This script extracts solar system and jump gate data from PostgreSQL,
transforms it into graph nodes and relationships, and loads it into Neo4j.

Graph Schema:
- Nodes: (:SolarSystem {id, name, security, region_id})
- Relationships: (:SolarSystem)-[:GATE]->(:SolarSystem)

Usage:
    python -m app.scripts.build_graph
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import engine
from app.graph import get_neo4j_driver


async def extract_solar_systems():
    """
    Extract solar system data from PostgreSQL.
    Returns list of (id, name, security, region_id) tuples.
    """
    print("📥 Extracting solar systems from PostgreSQL...")
    
    query = text("""
        SELECT 
            "solarSystemID" as id,
            "solarSystemName" as name,
            security,
            "regionID" as region_id
        FROM "mapSolarSystems"
        ORDER BY "solarSystemID"
    """)
    
    async with engine.begin() as conn:
        result = await conn.execute(query)
        systems = result.fetchall()
    
    print(f"✅ Extracted {len(systems):,} solar systems")
    return systems


async def extract_jump_gates():
    """
    Extract stargate connections from PostgreSQL.
    Returns list of (from_id, to_id) tuples.
    """
    print("📥 Extracting jump gates from PostgreSQL...")
    
    query = text("""
        SELECT 
            "fromSolarSystemID" as from_id,
            "toSolarSystemID" as to_id
        FROM "mapSolarSystemJumps"
        ORDER BY "fromSolarSystemID", "toSolarSystemID"
    """)
    
    async with engine.begin() as conn:
        result = await conn.execute(query)
        gates = result.fetchall()
    
    print(f"✅ Extracted {len(gates):,} jump gates")
    return gates


async def load_solar_systems_to_neo4j(systems: list, driver):
    """
    Load solar systems as nodes into Neo4j using batch UNWIND.
    """
    print("📤 Loading solar systems into Neo4j...")
    
    # Prepare data for batch insert
    nodes_data = [
        {
            "id": system.id,
            "name": system.name,
            "security": float(system.security) if system.security is not None else 0.0,
            "region_id": system.region_id
        }
        for system in systems
    ]
    
    # Batch insert using UNWIND
    query = """
    UNWIND $nodes AS node
    CREATE (s:SolarSystem {
        id: node.id,
        name: node.name,
        security: node.security,
        region_id: node.region_id
    })
    """
    
    async with driver.session() as session:
        # Clear existing data
        print("  🗑️  Clearing existing SolarSystem nodes...")
        await session.run("MATCH (s:SolarSystem) DETACH DELETE s")
        
        # Batch insert in chunks of 1000
        chunk_size = 1000
        for i in range(0, len(nodes_data), chunk_size):
            chunk = nodes_data[i:i + chunk_size]
            await session.run(query, nodes=chunk)
            print(f"  ✅ Loaded {min(i + chunk_size, len(nodes_data)):,}/{len(nodes_data):,} systems")
    
    print("✅ Solar systems loaded into Neo4j")


async def load_jump_gates_to_neo4j(gates: list, driver):
    """
    Load jump gates as relationships into Neo4j using batch UNWIND.
    """
    print("📤 Loading jump gates into Neo4j...")
    
    # Prepare data for batch insert
    rels_data = [
        {
            "from_id": gate.from_id,
            "to_id": gate.to_id
        }
        for gate in gates
    ]
    
    # Batch insert using UNWIND
    # Note: We create bidirectional relationships for symmetric travel
    query = """
    UNWIND $rels AS rel
    MATCH (from:SolarSystem {id: rel.from_id})
    MATCH (to:SolarSystem {id: rel.to_id})
    CREATE (from)-[:GATE]->(to)
    """
    
    async with driver.session() as session:
        # Batch insert in chunks of 1000
        chunk_size = 1000
        for i in range(0, len(rels_data), chunk_size):
            chunk = rels_data[i:i + chunk_size]
            await session.run(query, rels=chunk)
            print(f"  ✅ Loaded {min(i + chunk_size, len(rels_data)):,}/{len(rels_data):,} gates")
    
    print("✅ Jump gates loaded into Neo4j")


async def create_indexes(driver):
    """
    Create indexes for fast lookups.
    """
    print("📑 Creating indexes...")
    
    async with driver.session() as session:
        # Index on system ID (most common lookup)
        await session.run("CREATE INDEX IF NOT EXISTS FOR (s:SolarSystem) ON (s.id)")
        
        # Index on system name (for autocomplete)
        await session.run("CREATE INDEX IF NOT EXISTS FOR (s:SolarSystem) ON (s.name)")
        
        # Index on region (for regional queries)
        await session.run("CREATE INDEX IF NOT EXISTS FOR (s:SolarSystem) ON (s.region_id)")
    
    print("✅ Indexes created")


async def verify_graph(driver):
    """
    Verify the graph was built correctly.
    """
    print("\n🔍 Verifying graph structure...")
    
    async with driver.session() as session:
        # Count nodes
        result = await session.run("MATCH (s:SolarSystem) RETURN COUNT(s) AS count")
        record = await result.single()
        node_count = record["count"]
        print(f"  ✅ SolarSystem nodes: {node_count:,}")
        
        # Count relationships
        result = await session.run("MATCH ()-[g:GATE]->() RETURN COUNT(g) AS count")
        record = await result.single()
        rel_count = record["count"]
        print(f"  ✅ GATE relationships: {rel_count:,}")
        
        # Sample query: Jita connections
        result = await session.run("""
            MATCH (jita:SolarSystem {name: 'Jita'})
            MATCH (jita)-[:GATE]-(neighbor)
            RETURN COUNT(neighbor) AS neighbors
        """)
        record = await result.single()
        if record:
            print(f"  ✅ Jita has {record['neighbors']} neighboring systems")
        
        # Check for orphaned nodes
        result = await session.run("""
            MATCH (s:SolarSystem)
            WHERE NOT (s)-[:GATE]-()
            RETURN COUNT(s) AS orphans
        """)
        record = await result.single()
        orphans = record["orphans"]
        if orphans > 0:
            print(f"  ⚠️  Warning: {orphans} systems have no gate connections")
        else:
            print(f"  ✅ No orphaned systems")


async def main():
    """
    Main ETL workflow.
    """
    print("=" * 60)
    print("Neo4j Topology Graph Build Script")
    print("=" * 60)
    
    try:
        # Get Neo4j driver
        driver = await get_neo4j_driver()
        
        # Extract data from PostgreSQL
        systems = await extract_solar_systems()
        gates = await extract_jump_gates()
        
        # Load into Neo4j
        await load_solar_systems_to_neo4j(systems, driver)
        await load_jump_gates_to_neo4j(gates, driver)
        
        # Create indexes
        await create_indexes(driver)
        
        # Verify
        await verify_graph(driver)
        
        print("\n" + "=" * 60)
        print("✅ Graph Build Complete!")
        print("=" * 60)
        print("\nYou can now use the RouteService for pathfinding.")
        
    except Exception as e:
        print(f"\n❌ Error during graph build: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
