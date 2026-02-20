from rest_framework import permissions
from users.permissions import IsCommandStaff

class IsEvidenceActive(permissions.BasePermission):
    """
    Prevents modification of Evidence if the associated Case is CLOSED.
    Legal Requirement: Evidence in closed cases must be preserved as-is.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if hasattr(obj, 'case') and obj.case:
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
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if hasattr(obj, 'collected_by') and obj.collected_by == request.user:
            return True

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

        if obj.witness == request.user:
            if request.method in permissions.SAFE_METHODS:
                return True
            else:
                return False
        
        return False
