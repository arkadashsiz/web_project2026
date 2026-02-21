from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MostWantedViewSet, CivilianTipViewSet, RewardLookupView, BailViewSet

router = DefaultRouter()
router.register(r'most-wanted', MostWantedViewSet, basename='most-wanted')
router.register(r'tips', CivilianTipViewSet, basename='tips')
router.register(r'bail', BailViewSet, basename='bail')

urlpatterns = [
    path('', include(router.urls)),
    path('rewards/lookup/', RewardLookupView.as_view(), name='reward-lookup'),
]
