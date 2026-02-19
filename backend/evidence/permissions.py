from rest_framework import permissions
from users.permissions import IsCommandStaff

class IsEvidenceActive(permissions.BasePermission):
    """
    Prevents modification of Evidence if the associated Case is CLOSED.
    Legal Requirement: Evidence in closed cases must be preserved as-is.
    """
    def has_object_permission(self, request, view, obj):
        # 1. Read permissions are always allowed (subject to view-level checks)
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. Command Staff Override
        if IsCommandStaff().has_permission(request, view):
            return True

        # 3. Check Parent Case Status
        # Since Evidence models inherit, 'obj.case' is available on all types
        if hasattr(obj, 'case') and obj.case:
            # Re-using the logic from cases app regarding locked statuses
            locked_statuses = [
                'CLOSED_GUILTY', 
                'CLOSED_NOT_GUILTY', 
                'CLOSED_COLD', 
                'REJECTED'
            ]
            if obj.case.status in locked_statuses:
                return False

        return True


class IsCollectorOrCaseLead(permissions.BasePermission):
    """
    Determines who can EDIT evidence details.
    - The Officer who collected it (to fix typos/details).
    - The Lead Detective of the Case (to manage the investigation).
    - Command Staff (via override).
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed to authorized personnel
        if request.method in permissions.SAFE_METHODS:
            return True

        # Command Staff Override
        if IsCommandStaff().has_permission(request, view):
            return True

        # 1. Check if user is the one who collected it
        if hasattr(obj, 'collected_by') and obj.collected_by == request.user:
            return True

        # 2. Check if user is the Lead Detective on the case
        if hasattr(obj, 'case') and obj.case.lead_detective == request.user:
            return True

        return False


class IsWitnessOwner(permissions.BasePermission):
    """
    Specific to Testimony.
    Allows a Witness (Civilian) to VIEW their own testimony, 
    but NEVER edit it (to preserve police records).
    """
    def has_object_permission(self, request, view, obj):
        # Only relevant for Testimony objects
        if not hasattr(obj, 'witness'):
            return False

        # 1. Check if user is the witness
        if obj.witness == request.user:
            # 2. STRICTLY READ-ONLY for witnesses
            if request.method in permissions.SAFE_METHODS:
                return True
            else:
                return False # Witnesses cannot edit police records
        
        return False
