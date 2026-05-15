import redis.asyncio as aioredis

from app.config import REDIS_URL

def create_redis() -> aioredis.Redis:
    return aioredis.Redis.from_url(REDIS_URL, decode_responses=True)