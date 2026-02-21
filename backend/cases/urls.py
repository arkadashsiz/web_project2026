from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ComplaintViewSet, CrimeSceneReportViewSet

# If you have a CaseViewSet, import it as well:
# from .views import CaseViewSet

router = DefaultRouter()

# Register the viewsets
router.register(r'complaints', ComplaintViewSet, basename='complaint')
router.register(r'crime-scenes', CrimeSceneReportViewSet, basename='crime-scene')

# If you have a CaseViewSet created, register it like this:
# router.register(r'cases', CaseViewSet, basename='case')

urlpatterns = [
    path('', include(router.urls)),
]
