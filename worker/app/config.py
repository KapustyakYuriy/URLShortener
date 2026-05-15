import os

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.getenv('REDIS_PORT', "6379"))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CLICKS_RAW_CHANNEL = os.getenv('CLICKS_RAW_CHANNEL', 'clicks:raw')
CLICKS_ENRICHED_CHANNEL = os.getenv('CLICKS_ENRICHED_CHANNEL', 'clicks:enriched')

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
