import json
import redis
from datetime import datetime, timezone
from django.db.models import Count, QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated

from apps.urls.serializers import ShortURLSerializer
from apps.urls.models import ShortURL
from apps.urls.utils import generate_short_code

class IsOwner(BasePermission):
	def has_object_permission(self, request, view, obj):
		return obj.owner == request.user

class ShortURLViewSet(ModelViewSet):
	serializer_class = ShortURLSerializer
	permission_classes = [IsAuthenticated, IsOwner]

	def get_queryset(self)->QuerySet:
		if self.action == "list":
			return ShortURL.objects.filter(owner=self.request.user).annotate(
				click_count=Count("clickevent")
			)
		return ShortURL.objects.all().annotate(
			click_count=Count("clickevent")
		)

	def perform_create(self, serializer: BaseSerializer)->None:
		serializer.save(
			owner=self.request.user,
			short_code=generate_short_code(),
		)

class RedirectView(APIView):
	permission_classes = [AllowAny]

	def get(self, request: Request, short_code: str) -> HttpResponseRedirect:
		url = get_object_or_404(ShortURL, short_code=short_code)

		r = redis.Redis.from_url(settings.REDIS_URL)
		payload = json.dumps({
			"short_code": short_code,
			"ip_address": request.META.get("REMOTE_ADDR"),
			"user_agent": request.META.get("HTTP_USER_AGENT", ""),
			"clicked_at": datetime.now(timezone.utc).isoformat(),
		})
		r.publish(settings.CLICKS_RAW_CHANNEL, payload)
		r.close()

		return HttpResponseRedirect(url.original_url)
