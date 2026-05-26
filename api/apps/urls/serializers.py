from rest_framework import serializers

from apps.urls.models import ShortURL
from apps.analytics.models import ClickEvent

class ClickEventSerializer(serializers.ModelSerializer):
	class Meta:
		model = ClickEvent
		fields = ["clicked_at", "ip_address", "browser", "os", "device_type"]

class ShortURLSerializer(serializers.ModelSerializer):
	click_count = serializers.IntegerField(read_only=True)

	class Meta:
		model = ShortURL

		fields = ["id", "original_url", "short_code", "created_at", "click_count"]
		read_only_fields = ["short_code", "created_at"]

class ShortURLDetailSerializer(ShortURLSerializer):
	recent_clicks = serializers.SerializerMethodField()

	class Meta(ShortURLSerializer.Meta):
		fields = ShortURLSerializer.Meta.fields + ["recent_clicks"]

	def get_recent_clicks(self, obj):
		clicks = getattr(obj, "prefetched_clicks", None)
		if clicks is None:
			clicks = obj.clickevent_set.order_by("-clicked_at")[:10]
		else:
			clicks = clicks[:10]
		return ClickEventSerializer(clicks, many=True).data