from neo4j import GraphDatabase
import os
from app.logger import structlog

logger = structlog.get_logger()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_AUTH_STR = os.getenv("NEO4J_AUTH", "neo4j/password")

# Parse auth
try:
    user, password = NEO4J_AUTH_STR.split("/")
    NEO4J_AUTH = (user, password)
except ValueError:
    user = "neo4j"
    password = "password"
    NEO4J_AUTH = (user, password)
    logger.warning("neo4j_auth_parse_error", msg="Using default credentials", auth_str=NEO4J_AUTH_STR)


driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

def get_neo4j_driver():
    return driver

def close_neo4j_driver():
    driver.close()

def verify_connectivity():
    try:
        driver.verify_connectivity()
        return True
    except Exception as e:
        logger.error("neo4j_connection_failed", error=str(e))
        return False
