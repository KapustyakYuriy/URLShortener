import asyncio
import json
import redis.asyncio as aioredis
from loguru import logger
from user_agents import parse

from app.config import CLICKS_RAW_CHANNEL, LOG_LEVEL, CLICKS_ENRICHED_CHANNEL
from app.logging_setup import setup_loguru_sink
from app.redis_client import create_redis

async def enrich(redis: aioredis.Redis, data: str) -> None:
    try:
        event = json.loads(data)
    except json.JSONDecodeError:
        logger.warning("invalid JSON received | data={}", data)
        return
    
    ua = parse(event.get("user_agent", ""))
    event["browser"] = ua.browser.family
    event["os"] = ua.os.family
    event["device_type"] = "tablet" if ua.is_tablet else "mobile" if ua.is_mobile else "desktop"

    logger.info(
        "enriched | short_code={} browser={} os={} device={}",
        event.get("short_code"), event["browser"], event["os"], event["device_type"]
    )

    await redis.publish(CLICKS_ENRICHED_CHANNEL, json.dumps(event))

async def run() -> None:
    redis = create_redis()
    try:
        pubsub = redis.pubsub()
        await pubsub.subscribe(CLICKS_RAW_CHANNEL)
        logger.info("worker started | subscribed to {}", CLICKS_RAW_CHANNEL)

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            asyncio.create_task(enrich(redis, message["data"]))
    finally:
        await redis.aclose()


def main() -> None:
    setup_loguru_sink(LOG_LEVEL)
    asyncio.run(run())


if __name__ == "__main__":
    main()

