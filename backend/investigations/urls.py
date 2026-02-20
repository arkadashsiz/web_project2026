from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DetectiveBoardViewSet, 
    InvestigationOperationsViewSet, 
    SergeantReviewViewSet, 
    JudicialViewSet, 
    MostWantedViewSet
)

router = DefaultRouter()

# Detective Board (Evidence linking)
router.register(r'board', DetectiveBoardViewSet, basename='detective-board')

# Operations (Interrogation, Submission)
router.register(r'operations', InvestigationOperationsViewSet, basename='suspect-ops')

# Sergeant Review (Approvals)
router.register(r'reviews', SergeantReviewViewSet, basename='sergeant-review')

# Judicial (Trials)
router.register(r'trials', JudicialViewSet, basename='trials')

# High Command (Most Wanted List)
router.register(r'most-wanted', MostWantedViewSet, basename='most-wanted')

urlpatterns = [
    path('', include(router.urls)),
]
