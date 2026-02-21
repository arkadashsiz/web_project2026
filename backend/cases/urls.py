from rest_framework.routers import DefaultRouter
from .views import CaseViewSet, ComplaintSubmissionViewSet, CaseComplainantViewSet, CaseWitnessViewSet

router = DefaultRouter()
router.register('cases', CaseViewSet, basename='cases')
router.register('complaint-submissions', ComplaintSubmissionViewSet, basename='complaint-submissions')
router.register('case-complainants', CaseComplainantViewSet, basename='case-complainants')
router.register('case-witnesses', CaseWitnessViewSet, basename='case-witnesses')

urlpatterns = router.urls
