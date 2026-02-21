# investigation/permissions.py
from rest_framework import permissions

class BaseRolePermission(permissions.BasePermission):
    required_level = 0
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'access_level', 0) >= self.required_level
        )

class IsDetective(BaseRolePermission):
    required_level = 40

class IsSergeant(BaseRolePermission):
    required_level = 60

class IsJudge(BaseRolePermission):
    required_level = 70

class IsCaptain(BaseRolePermission):
    required_level = 80

class IsChief(BaseRolePermission):
    required_level = 90
