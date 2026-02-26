from rest_framework import permissions, viewsets
from rest_framework.response import Response
from .models import Role, UserRole
from .serializers import RoleSerializer, UserRoleSerializer


class SuperuserOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.prefetch_related('permissions').all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = [SuperuserOnly]

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        removed_assignments = role.user_roles.count()
        role_name = role.name
        role.delete()
        return Response({
            'detail': f'Role "{role_name}" deleted.',
            'removed_user_roles': removed_assignments,
        })


class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.select_related('user', 'role').all().order_by('id')
    serializer_class = UserRoleSerializer
    permission_classes = [SuperuserOnly]
