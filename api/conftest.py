import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.urls.models import ShortURL
from apps.urls.utils import generate_short_code

@pytest.fixture
def api_client():
	return APIClient()

@pytest.fixture
def user(db):
	return User.objects.create_user(username="testuser", password="testpass123")

@pytest.fixture
def auth_client(api_client, user):
	api_client.force_authenticate(user=user)
	return api_client

@pytest.fixture
def short_url(user, db):
	return ShortURL.objects.create(
		owner=user,
		original_url="https://example.com",
		short_code=generate_short_code(),
	)