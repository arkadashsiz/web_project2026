from rest_framework.routers import DefaultRouter
from .views import TipViewSet, RewardClaimViewSet

router = DefaultRouter()
router.register('tips', TipViewSet, basename='tips')
router.register('reward-claims', RewardClaimViewSet, basename='reward-claims')

urlpatterns = router.urls
