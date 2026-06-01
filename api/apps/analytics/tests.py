import pytest
from django.utils import timezone
from apps.analytics.models import ClickEvent

@pytest.mark.django_db
class TestAnalytics:
	def test_stats(self, auth_client, short_url):
		ClickEvent.objects.create(
			short_url=short_url,
			clicked_at=timezone.now(),
			ip_address="127.0.0.1",
			user_agent="Mozilla",
			browser="Chrome",
			os="Windows",
			device_type="desktop",
		)
		response = auth_client.get(f"/api/urls/{short_url.id}/stats/")
		assert response.status_code == 200
		assert "total_clicks" in response.data
		assert "clicks_per_day" in response.data
		assert "top_browsers" in response.data
		assert "top_os" in response.data

	def test_summary(self, auth_client, short_url):
		response = auth_client.get("/api/stats/summary/")
		assert response.status_code == 200
		assert "total_urls" in response.data
		assert "total_clicks" in response.data
		assert "top_urls" in response.data
