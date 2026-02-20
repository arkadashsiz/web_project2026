from rest_framework import permissions

class IsDetective(permissions.BasePermission):
    """ Allows access to Detectives (Level 40+). """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.access_level >= 40

class IsSergeant(permissions.BasePermission):
    """ Allows access to Sergeants (Level 60+) for approvals. """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.access_level >= 60

class IsJudge(permissions.BasePermission):
    """ Allows access to Judges (Level 70+) for trials. """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.access_level >= 70

class IsHighCommand(permissions.BasePermission):
    """ Allows access to High Command (Level 80+). """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.access_level >= 80
