import json
import redis
from datetime import timedelta
from django.db.models import Count, QuerySet, Prefetch
from django.db.models.functions import TruncDate
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.urls.serializers import ShortURLSerializer, ShortURLDetailSerializer
from apps.urls.models import ShortURL
from apps.urls.utils import generate_short_code
from apps.analytics.models import ClickEvent

class IsOwner(BasePermission):
	def has_object_permission(self, request, view, obj):
		return obj.owner == request.user

class ShortURLViewSet(ModelViewSet):
	serializer_class = ShortURLSerializer
	permission_classes = [IsAuthenticated, IsOwner]

	def get_serializer_class(self):
		if self.action == "retrieve":
			return ShortURLDetailSerializer
		return ShortURLSerializer

	def get_queryset(self)->QuerySet:
		if self.action == "list":
			return ShortURL.objects.filter(owner=self.request.user).annotate(
				click_count=Count("clickevent")
			)
		if self.action == "retrieve":
			return ShortURL.objects.annotate(
				click_count=Count("clickevent")
			).prefetch_related(
				Prefetch(
					"clickevent_set",
					queryset=ClickEvent.objects.order_by("-clicked_at"),
					to_attr="prefetched_clicks",
				)
			)
		return ShortURL.objects.all().annotate(
			click_count=Count("clickevent")
		).order_by("-created_at")

	def perform_create(self, serializer: BaseSerializer)->None:
		serializer.save(
			owner=self.request.user,
			short_code=generate_short_code(),
		)
	
	@action(detail=True, methods=["get"])
	def stats(self, request: Request, pk=None)->Response:
		url = self.get_object()
		clicks = ClickEvent.objects.filter(short_url=url)
		total_clicks = clicks.count()

		since = (timezone.now() - timedelta(days=29)).date()
		today = timezone.now().date()

		clicks_by_day = {
			row["date"]: row["count"]
			for row in clicks.filter(clicked_at__date__gte=since)
			.annotate(date=TruncDate("clicked_at"))
			.values("date")
			.annotate(count=Count("id"))
		}

		current = since
		clicks_per_day = []
		while current <= today:
			clicks_per_day.append({"date": current, "count": clicks_by_day.get(current, 0)})
			current += timedelta(days=1)

		top_browsers = list(clicks.values("browser").annotate(count=Count("id")).order_by("-count")[:5])
		top_os = list(clicks.values("os").annotate(count=Count("id")).order_by("-count")[:5])
		
		return Response({
			"total_clicks": total_clicks,
			"clicks_per_day": clicks_per_day,
			"top_browsers": top_browsers,
			"top_os": top_os,
		})

	@action(detail=False, methods=["get"])
	def summary(self, request: Request)->Response:
		urls = ShortURL.objects.filter(owner=request.user)
		total_urls = urls.count()
		total_clicks = ClickEvent.objects.filter(short_url__owner=request.user).count()

		top_urls = list(
			urls.annotate(click_count=Count("clickevent"))
			.order_by("-click_count")[:5]
			.values("id", "short_code", "original_url", "click_count")
		)

		return Response({
			"total_urls": total_urls,
			"total_clicks": total_clicks,
			"top_urls": top_urls,
		})


class RedirectView(APIView):
	permission_classes = [AllowAny]

	def get(self, request: Request, short_code: str) -> HttpResponseRedirect:
		url = get_object_or_404(ShortURL, short_code=short_code)

		r = redis.Redis.from_url(settings.REDIS_URL)
		payload = json.dumps({
			"short_code": short_code,
			"ip_address": request.META.get("REMOTE_ADDR"),
			"user_agent": request.META.get("HTTP_USER_AGENT", ""),
			"clicked_at": timezone.now().isoformat(),
		})
		r.publish(settings.CLICKS_RAW_CHANNEL, payload)
		r.close()

		return HttpResponseRedirect(url.original_url)
