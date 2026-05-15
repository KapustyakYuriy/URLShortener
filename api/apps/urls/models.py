from django.db import models
from django.conf import settings

class ShortURL(models.Model):
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
	)
	original_url = models.URLField()
	short_code = models.CharField(
		max_length=8,
		unique=True,
	)
	created_at = models.DateTimeField(
		auto_now_add=True
	)