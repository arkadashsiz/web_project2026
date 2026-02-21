from rest_framework import permissions, viewsets
from .models import Role, UserRole
from .serializers import RoleSerializer, UserRoleSerializer


class SuperuserOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.prefetch_related('permissions').all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = [SuperuserOnly]


class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.select_related('user', 'role').all().order_by('id')
    serializer_class = UserRoleSerializer
    permission_classes = [SuperuserOnly]
