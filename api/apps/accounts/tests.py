import pytest

@pytest.mark.django_db
class TestRegister:
	url = "/api/auth/register/"

	def test_success(self, api_client):
		response = api_client.post(self.url, {"username": "user", "password": "strongpass123"})
		assert response.status_code == 201
		assert "access" in response.data
		assert "refresh" in response.data

	def test_duplicate_username(self, api_client, user):
		response = api_client.post(self.url, {"username": "testuser", "password": "strongpass123"})
		assert response.status_code == 400
	
	def test_missing_fields(self, api_client):
		response = api_client.post(self.url, {"username": "user"})
		assert response.status_code == 400

@pytest.mark.django_db
class TestLogin:
	url = "/api/auth/login/"

	def test_success(self, api_client, user):
		response = api_client.post(self.url, {"username": "testuser", "password": "testpass123"})
		assert response.status_code == 200
		assert "access" in response.data
		assert "refresh" in response.data

	def test_wrong_password(self, api_client, user):
		response = api_client.post(self.url, {"username": "testuser", "password": "wrongpass123"})
		assert response.status_code == 401

@pytest.mark.django_db
class TestRefresh:
	url = "/api/auth/refresh/"

	def test_success(self, api_client, user):
		refresh = api_client.post("/api/auth/login/", {"username": "testuser", "password": "testpass123"}).data["refresh"]
		response = api_client.post(self.url, {"refresh": refresh})
		assert response.status_code == 200
		assert "access" in response.data
		assert "refresh" in response.data

	def test_invalid_refreshtoken(self, api_client):
		response = api_client.post(self.url, {"refresh": "fake token"})
		assert response.status_code == 401
