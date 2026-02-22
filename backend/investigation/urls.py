from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    DetectiveBoardViewSet,
    BoardNodeViewSet,
    BoardEdgeViewSet,
    SuspectViewSet,
    InterrogationViewSet,
    NotificationViewSet,
    SuspectSubmissionViewSet,
    high_alert_list,
)

router = DefaultRouter()
router.register('boards', DetectiveBoardViewSet, basename='boards')
router.register('board-nodes', BoardNodeViewSet, basename='board-nodes')
router.register('board-edges', BoardEdgeViewSet, basename='board-edges')
router.register('suspects', SuspectViewSet, basename='suspects')
router.register('suspect-submissions', SuspectSubmissionViewSet, basename='suspect-submissions')
router.register('interrogations', InterrogationViewSet, basename='interrogations')
router.register('notifications', NotificationViewSet, basename='notifications')

urlpatterns = router.urls + [
    path('high-alert/', high_alert_list),
]
