from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TestimonyViewSet,
    BiologicalViewSet,
    VehicleViewSet,
    IDDocumentViewSet
)

# Initialize the DefaultRouter
router = DefaultRouter()

# Register each evidence type ViewSet with a clear, pluralized endpoint name
router.register(r'testimonies', TestimonyViewSet, basename='testimony')
router.register(r'biological', BiologicalViewSet, basename='biological')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'id-documents', IDDocumentViewSet, basename='id-document')

# The router automatically generates all standard REST API routes
urlpatterns = [
    path('', include(router.urls)),
]
