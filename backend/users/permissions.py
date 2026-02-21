from rest_framework import permissions


class IsPolicePersonnel(permissions.BasePermission):
    """
    Allows access to basic police tools.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_police)


class IsOfficerOrHigher(permissions.BasePermission):
    """
    Level >= 20. Officers, Detectives, Sergeants, Command.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.highest_access_level >= 20)


class IsDetectiveOrHigher(permissions.BasePermission):
    """
    Level >= 40. For sensitive case files and evidence management.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.highest_access_level >= 40)


class IsSergeantOrHigher(permissions.BasePermission):
    """
    Level >= 60. For assigning cases and supervising personnel.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.highest_access_level >= 60)


class IsJudge(permissions.BasePermission):
    """
    Level == 70. Judiciary specific access (Warrants).
    """
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False

        if request.user.highest_access_level == 70:
            return True

        return request.user.has_role('Judge') or request.user.has_role('قاضی')


class IsCommandStaff(permissions.BasePermission):
    """
    Level >= 80 (Captain, Chief). Full station admin control.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.highest_access_level >= 80)


class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj == request.user)


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsAccountOwnerOrSuperUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and (obj == request.user or request.user.is_superuser))


class IsAccountOwnerOrCommand(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not bool(request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        if request.user.highest_access_level >= 80:
            return True

        return obj == request.user
