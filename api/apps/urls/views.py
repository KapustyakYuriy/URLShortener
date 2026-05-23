from django.db.models import Count, QuerySet
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import BaseSerializer

from apps.urls.serializers import ShortURLSerializer
from apps.urls.models import ShortURL
from apps.urls.utils import generate_short_code

class ShortURLViewSet(ModelViewSet):
	serializer_class = ShortURLSerializer

	def get_queryset(self)->QuerySet:
		return ShortURL.objects.filter(owner=self.request.user).annotate(
			click_count=Count("clickevent")
		)

	def perform_create(self, serializer: BaseSerializer)->None:
		serializer.save(
			owner=self.request.user,
			short_code=generate_short_code(),
		)
