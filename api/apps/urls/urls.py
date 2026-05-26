from rest_framework.routers import DefaultRouter

from apps.urls.views import ShortURLViewSet

router = DefaultRouter()
router.register("", ShortURLViewSet, basename="shorturl")

urlpatterns = router.urls