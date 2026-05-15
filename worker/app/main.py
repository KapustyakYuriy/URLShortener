import asyncio

from loguru import logger

from app.config import CLICKS_RAW_CHANNEL, LOG_LEVEL
from app.logging_setup import setup_loguru_sink
from app.redis_client import create_redis


async def run() -> None:
    redis = create_redis()
    try:
        pubsub = redis.pubsub()
        await pubsub.subscribe(CLICKS_RAW_CHANNEL)
        logger.info("worker started | subscribed to {}", CLICKS_RAW_CHANNEL)

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            logger.info("received message | data={}", message["data"])
    finally:
        await redis.aclose()


def main() -> None:
    setup_loguru_sink(LOG_LEVEL)
    asyncio.run(run())


if __name__ == "__main__":
    main()

