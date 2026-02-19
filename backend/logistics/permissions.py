from rest_framework import permissions
from users.permissions import IsCommandStaff

class IsTipOwnerOrPolice(permissions.BasePermission):
    """
    Controls access to Tips.
    - Informants: Can view THEIR OWN tips. Can only edit if status is PENDING.
    - Police: Can view ALL tips. Can edit status/reward (Detectives+).
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is police (Access Level >= 10)
        is_police = request.user.role and request.user.role.access_level >= 10

        # 1. READ Access
        if request.method in permissions.SAFE_METHODS:
            if is_police:
                return True
            # Civilian: Must be the informant
            return obj.informant == request.user

        # 2. WRITE Access (Update/Delete)
        if is_police:
            # Detectives (Level >= 40) or Command Staff can manage tips (set rewards/status)
            if request.user.role.access_level >= 40:
                return True
            return False

        # Civilian: Can only edit if they own it AND it hasn't been processed yet
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
        # 1. READ Access
        if request.method in permissions.SAFE_METHODS:
            # Police/Admin can view all
            if request.user.role and request.user.role.access_level >= 10:
                return True
            # Suspects can view their own payments
            # Note: Payment links to CaseSuspect, which links to User (suspect)
            if hasattr(obj, 'case_suspect') and obj.case_suspect.suspect == request.user:
                return True
            return False

        # 2. WRITE Access
        # Suspects can NEVER edit a payment record (must go through payment gateway or clerk)
        if obj.case_suspect.suspect == request.user:
            return False

        # Only Command Staff (Level >= 80) or Superusers can manually alter payment records
        # (e.g., voiding a transaction or confirming a manual cash payment)
        if IsCommandStaff().has_permission(request, view):
            return True
            
        return False
