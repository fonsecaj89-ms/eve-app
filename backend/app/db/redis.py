import redis.asyncio as redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Create a connection pool
pool = redis.ConnectionPool(host=REDIS_HOST, port=int(REDIS_PORT), decode_responses=True)

# Function to get a redis client
def get_redis_client():
    return redis.Redis(connection_pool=pool)

async def check_redis_connection():
    try:
        r = get_redis_client()
        await r.ping()
        return True
    except Exception:
        return False
