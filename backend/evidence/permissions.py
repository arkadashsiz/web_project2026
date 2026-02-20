from rest_framework import permissions
from users.permissions import IsCommandStaff


class IsEvidenceActive(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if IsCommandStaff().has_permission(request, view):
            return True
        if hasattr(obj, 'case') and obj.case:
            locked_statuses = ['CLOSED_GUILTY', 'CLOSED_NOT_GUILTY', 'CLOSED_COLD', 'REJECTED']
            if getattr(obj.case, 'status', None) in locked_statuses:
                return False
        return True


class IsCollectorOrCaseLead(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if IsCommandStaff().has_permission(request, view):
            return True
        if hasattr(obj, 'collected_by') and obj.collected_by == request.user:
            return True
        if hasattr(obj, 'case') and getattr(obj.case, 'lead_detective', None) == request.user:
            return True
        return False


class IsWitnessOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.access_level >= 20:
            return True

        if not hasattr(obj, 'witness'):
            return False

        if obj.witness == request.user:
            return request.method in permissions.SAFE_METHODS

        return False

from users.permissions import IsCommandStaff


class IsOwnerOrPolice(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if IsCommandStaff().has_permission(request, view) or getattr(request.user, "access_level", 0) >= 20:
            return True
        return obj.submitted_by == request.user
    

