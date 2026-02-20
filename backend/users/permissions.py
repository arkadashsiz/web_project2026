from rest_framework import permissions

# ==========================================================
# 1. HIERARCHICAL ROLE PERMISSIONS (Global Access)
# ==========================================================

class IsPolicePersonnel(permissions.BasePermission):
    """
    Level >= 10. Allows access to basic police tools.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
        return request.user.role.access_level >= 10

class IsOfficerOrHigher(permissions.BasePermission):
    """
    Level >= 20. Officers, Detectives, Sergeants, Command.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
        return request.user.role.access_level >= 20

class IsDetectiveOrHigher(permissions.BasePermission):
    """
    Level >= 40. For sensitive case files and evidence management.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
        return request.user.role.access_level >= 40

class IsSergeantOrHigher(permissions.BasePermission):
    """
    Level >= 60. For assigning cases and supervising personnel.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
        return request.user.role.access_level >= 60

class IsJudge(permissions.BasePermission):
    """
    Level == 70. Judiciary specific access (Warrants).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
        return request.user.role.access_level == 70

class IsCommandStaff(permissions.BasePermission):
    """
    Level >= 80 (Captain, Chief). Full station admin control.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
        return request.user.role.access_level >= 80

# ==========================================================
# 2. OBJECT-LEVEL PERMISSIONS (Owner Checks)
# ==========================================================

class IsAccountOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object (User Profile) to edit it.
    Assumes the model instance has an attribute `id` matching the user.
    """
    def has_object_permission(self, request, view, obj):
        return obj == request.user

class IsAccountOwner(permissions.BasePermission):
    """
    Allows a user to edit their own profile.
    Allows Admins/Chief (Level >= 90) to edit ANY profile.
    """
    def has_object_permission(self, request, view, obj):
        if obj == request.user:
            return True
            
        return False

class IsSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow access to superusers.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
