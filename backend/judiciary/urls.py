from rest_framework.routers import DefaultRouter
from .views import CourtSessionViewSet

router = DefaultRouter()
router.register('court-sessions', CourtSessionViewSet, basename='court-sessions')

urlpatterns = router.urls
