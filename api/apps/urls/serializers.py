from rest_framework import serializers
from apps.urls.models import ShortURL

class ShortURLSerializer(serializers.ModelSerializer):
	click_count = serializers.IntegerField(read_only=True)

	class Meta:
		model = ShortURL

		fields = ["id", "original_url", "short_code", "created_at", "click_count"]
		read_only_fields = ["short_code", "created_at"]