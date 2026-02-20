from rest_framework import permissions
from users.permissions import IsCommandStaff

class IsTipOwnerOrPolice(permissions.BasePermission):
    """
    Controls access to Tips.
    - Informants: Can view THEIR OWN tips. Can only edit if status is PENDING.
    - Police: Can view ALL tips. Can edit status/reward (Detectives+).
    """
    def has_object_permission(self, request, view, obj):
        is_police = request.user.role and request.user.role.access_level >= 10

        if request.method in permissions.SAFE_METHODS:
            if is_police:
                return True
            return obj.informant == request.user

        if is_police:
            if request.user.role.access_level >= 40:
                return True
            return False

        if obj.informant == request.user:
            if obj.status == 'PENDING':
                return True
            
        return False


class IsPaymentRelatedOrAdmin(permissions.BasePermission):
    """
    Controls access to Payments (Bail/Fines).
    - Suspects: Can VIEW their own payments. CANNOT edit.
    - Police: Can VIEW all payments.
    - Command/Admin: Can manually update payment status (e.g. if paid in cash).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if request.user.role and request.user.role.access_level >= 10:
                return True
            if hasattr(obj, 'case_suspect') and obj.case_suspect.suspect == request.user:
                return True
            return False

        if obj.case_suspect.suspect == request.user:
            return False

        if IsCommandStaff().has_permission(request, view):
            return True
            
        return False
