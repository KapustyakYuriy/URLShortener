from django.db import models
from apps.urls.models import ShortURL

# Create your models here.
class ClickEvent(models.Model):
	short_url = models.ForeignKey(
		ShortURL,
		on_delete=models.CASCADE
	)
	clicked_at = models.DateTimeField(
		auto_now_add=True,
		db_index=True
	)
	ip_address = models.CharField(
		max_length=45
	)
	user_agent = models.CharField(
		max_length=512
	)
	browser = models.CharField(
		max_length=50
	)
	os = models.CharField(
		max_length=50
	)
	device_type = models.CharField(
		max_length=20
	)