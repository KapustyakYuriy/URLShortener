import json
import pytest
import asyncio
import fakeredis.aioredis
from app.main import enrich

@pytest.mark.asyncio
async def test_enrich_valid_event():
	redis = fakeredis.aioredis.FakeRedis()
	pubsub = redis.pubsub()
	await pubsub.subscribe("clicks:enriched")
	await pubsub.get_message()

	data = json.dumps({
		"short_code": "abc123",
		"ip_address": "127.0.0.1",
		"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
		"clicked_at": "2026-05-31T10:00:00+00:00",
	})
	await enrich(redis, data)

	message = await asyncio.wait_for(
		pubsub.get_message(ignore_subscribe_messages=True, timeout=1),
		timeout=2,
	)

	assert message is not None
	result = json.loads(message["data"])
	assert "browser" in result
	assert "os" in result
	assert "device_type" in result

@pytest.mark.asyncio
async def test_enrich_invalid_json_does_not_crash():
	redis = fakeredis.aioredis.FakeRedis()
	await enrich(redis, "not valid json")
