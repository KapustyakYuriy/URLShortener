import pytest
import django.db
import django.test.utils
from django.utils import timezone
from apps.urls.models import ShortURL
from apps.urls.utils import generate_short_code
from apps.analytics.models import ClickEvent

@pytest.mark.django_db
class TestShort:
	def test_create(self, auth_client):
		response = auth_client.post("/api/urls/", {"original_url": "https://example.com"})
		assert response.status_code == 201
		assert "short_code" in response.data

	def test_list_has_click_count(self, auth_client, short_url):
		response = auth_client.get("/api/urls/")
		assert response.status_code == 200
		assert "click_count" in response.data["results"][0]

	def test_retrieve_has_recent_clicks(self, auth_client, short_url):
		response = auth_client.get(f"/api/urls/{short_url.id}/")
		assert response.status_code == 200
		assert "recent_clicks" in response.data

	def test_delete_owner(self, auth_client, short_url):
		response = auth_client.delete(f"/api/urls/{short_url.id}/")
		assert response.status_code == 204
	
	def test_delete_non_owner(self, api_client, short_url):
		other_user_client = api_client
		from django.contrib.auth.models import User
		other = User.objects.create_user(username="other", password="pass123456")
		other_user_client.force_authenticate(user=other)
		response = other_user_client.delete(f"/api/urls/{short_url.id}/")
		assert response.status_code == 404
	
@pytest.mark.django_db
class TestRedirect:
	def test_redirect(self, api_client, short_url):
		response = api_client.get(f"/{short_url.short_code}/")
		assert response.status_code == 302
		assert response["Location"] == short_url.original_url

	def test_invalid_code(self, api_client):
		response = api_client.get("/invalidcode/")
		assert response.status_code == 404

@pytest.mark.django_db
class TestQueryCount:
	def test_short_url_list_query_count_is_constant(self, auth_client, user):
		ShortURL.objects.create(
			owner=user,
			original_url="https://example.com",
			short_code=generate_short_code(),
		)

		with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx_1:
			auth_client.get("/api/urls/")

		for _ in range(19):
			ShortURL.objects.create(
				owner=user,
				original_url="https://example.com",
				short_code=generate_short_code(),
			)

		with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx_20:
			auth_client.get("/api/urls/")

		assert len(ctx_1) == len(ctx_20)

	def test_short_url_retrieve_query_count_is_constant(self, auth_client, user, short_url):
		with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx0:
			auth_client.get(f"/api/urls/{short_url.id}/")

		for _ in range(20):
			ClickEvent.objects.create(
				short_url=short_url,
				clicked_at=timezone.now(),
				ip_address="127.0.0.1",
				user_agent="Mozilla",
				browser="Chrome",
				os="Windows",
				device_type="desktop",
			)
			
		with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx20:
			auth_client.get(f"/api/urls/{short_url.id}/")

		assert len(ctx0) == len(ctx20)
