from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, UserRoleViewSet

router = DefaultRouter()
router.register('roles', RoleViewSet, basename='roles')
router.register('user-roles', UserRoleViewSet, basename='user-roles')

urlpatterns = router.urls
