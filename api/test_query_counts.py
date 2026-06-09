import pytest
import django.db
import django.test.utils


@pytest.mark.django_db
class TestQueryCounts:
		def test_register(self, api_client):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				api_client.post("/api/auth/register/", {"username": "newuser", "password": "strongpass123"})
			#print(f"\nPOST /api/auth/register/: {len(ctx)}")
			assert len(ctx) == 2

		def test_login(self, api_client, user):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				api_client.post("/api/auth/login/", {"username": "testuser", "password": "testpass123"})
			#print(f"\nPOST /api/auth/login/: {len(ctx)}")
			assert len(ctx) == 2

		def test_refresh(self, api_client, user):
			refresh = api_client.post("/api/auth/login/", {"username": "testuser", "password": "testpass123"}).data["refresh"]
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				api_client.post("/api/auth/refresh/", {"refresh": refresh})
			#print(f"\nPOST /api/auth/refresh/: {len(ctx)}")
			assert len(ctx) == 13

		def test_create_url(self, auth_client):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				auth_client.post("/api/urls/", {"original_url": "https://example.com"})
			#print(f"\nPOST /api/urls/: {len(ctx)}")
			assert len(ctx) == 2

		def test_list_urls(self, auth_client, short_url):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				auth_client.get("/api/urls/")
			#print(f"\nGET /api/urls/: {len(ctx)}")
			assert len(ctx) == 2

		def test_retrieve_url(self, auth_client, short_url):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				auth_client.get(f"/api/urls/{short_url.id}/")
			#print(f"\nGET /api/urls/{{id}}/: {len(ctx)}")
			assert len(ctx) == 3

		def test_delete_url(self, auth_client, short_url):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				auth_client.delete(f"/api/urls/{short_url.id}/")
			#print(f"\nDELETE /api/urls/{{id}}/: {len(ctx)}")
			assert len(ctx) == 4

		def test_redirect(self, api_client, short_url):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				api_client.get(f"/{short_url.short_code}/")
			#print(f"\nGET /{{short_code}}/: {len(ctx)}")
			assert len(ctx) == 1

		def test_stats(self, auth_client, short_url):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				auth_client.get(f"/api/urls/{short_url.id}/stats/")
			#print(f"\nGET /api/urls/{{id}}/stats/: {len(ctx)}")
			assert len(ctx) == 6

		def test_summary(self, auth_client, short_url):
			with django.test.utils.CaptureQueriesContext(django.db.connection) as ctx:
				auth_client.get("/api/stats/summary/")
			#print(f"\nGET /api/stats/summary/: {len(ctx)}")
			assert len(ctx) == 3