import pytest

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
		assert response.status_code == 403
	