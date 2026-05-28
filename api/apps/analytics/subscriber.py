import redis
import json
from loguru import logger
from django.conf import settings

from apps.urls.models import ShortURL
from apps.analytics.models import ClickEvent

def run_subscriber() -> None:
	r = redis.Redis.from_url(settings.REDIS_URL)
	pubsub = r.pubsub()
	pubsub.subscribe(settings.CLICKS_ENRICHED_CHANNEL)

	logger.info("subscriber started | listening to {}", settings.CLICKS_ENRICHED_CHANNEL)

	for message in pubsub.listen():
		if message["type"] != "message":
			continue
		try:
			event = json.loads(message["data"])
			short_url = ShortURL.objects.get(short_code=event["short_code"])
			ClickEvent.objects.create(
				short_url=short_url,
				clicked_at=event["clicked_at"],
				ip_address=event.get("ip_address", ""),
				user_agent=event.get("user_agent", ""),
				browser=event.get("browser", ""),
				os=event.get("os", ""),
				device_type=event.get("device_type", ""),
			)
			logger.info(
				"click saved | short_code={} browser={} os={} device={} ip={}",
				event.get("short_code"), event.get("browser"), event.get("os"),
				event.get("device_type"), event.get("ip_address"),
			)
		except Exception as e:
			logger.warning(
				"failed to save click | error={}", e
			)