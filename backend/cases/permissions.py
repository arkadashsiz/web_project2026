from rest_framework import permissions
from users.permissions import IsCommandStaff


class IsCaseReadOnlyIfClosed(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        locked_statuses = [
            'CLOSED_GUILTY',
            'CLOSED_NOT_GUILTY',
            'CLOSED_COLD',
            'REJECTED'
        ]

        if hasattr(obj, 'status') and obj.status in locked_statuses:
            return False

        return True


class IsLeadDetectiveOrCommand(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if hasattr(obj, 'lead_detective') and obj.lead_detective == request.user:
            return True

        return False


class IsComplaintOwnerOrPolice(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        is_police = getattr(user, 'access_level', 0) >= 10

        if request.method in permissions.SAFE_METHODS:
            return True if is_police else obj.complainant == user

        if is_police:
            return True

        if obj.complainant == user and obj.status in [
            'PENDING_CADET',
            'PENDING_OFFICER',
            'RETURNED_TO_COMPLAINANT',
        ]:
            return True

        return False


class IsReportAuthorOrCommand(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if hasattr(obj, 'reporting_officer') and obj.reporting_officer == request.user:
            return True

        return False
