from rest_framework.routers import DefaultRouter
from .views import (
    WitnessEvidenceViewSet,
    BiologicalEvidenceViewSet,
    VehicleEvidenceViewSet,
    IdentificationEvidenceViewSet,
    OtherEvidenceViewSet,
)

router = DefaultRouter()
router.register('witness', WitnessEvidenceViewSet, basename='witness-evidence')
router.register('biological', BiologicalEvidenceViewSet, basename='biological-evidence')
router.register('vehicle', VehicleEvidenceViewSet, basename='vehicle-evidence')
router.register('identification', IdentificationEvidenceViewSet, basename='identification-evidence')
router.register('other', OtherEvidenceViewSet, basename='other-evidence')

urlpatterns = router.urls
