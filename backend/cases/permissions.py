from rest_framework import permissions
from users.permissions import IsCommandStaff

class IsCaseReadOnlyIfClosed(permissions.BasePermission):
    """
    Prevents modification of Cases that are marked as CLOSED, ARCHIVED, or REJECTED.
    Only Command Staff (Captain/Chief) can reopen/edit a closed case.
    """
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
    """
    Strict Object-Level Permission for Case Management.
    - Allows the 'lead_detective' to edit the case.
    - Allows Command Staff (Level >= 80) to edit.
    - Assigned Personnel (but not Lead) usually have Read-Only or limited update rights 
      (handled by Views logic, but here we define ownership).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if hasattr(obj, 'lead_detective') and obj.lead_detective == request.user:
            return True
            
        return False


class IsComplaintOwnerOrPolice(permissions.BasePermission):
    """
    Handles permissions for Complaints (Civilians vs Police).
    - Civilians: Can view THEIR OWN complaints. Can create.
    - Police: Can view ALL complaints.
    - Editing: 
        - Civilians can only edit if status is 'PENDING'.
        - Police (Sergeants+) usually edit status to Approve/Reject.
    """
    def has_object_permission(self, request, view, obj):
        is_police = False
        if request.user.role and request.user.role.access_level >= 10:
            is_police = True

        if request.method in permissions.SAFE_METHODS:
            if is_police:
                return True
            return obj.complainant == request.user

        if is_police:
            return True
        
        if obj.complainant == request.user:
            if obj.status == 'PENDING':
                return True
            
        return False


class IsReportAuthorOrCommand(permissions.BasePermission):
    """
    For CrimeSceneReport.
    - Only the Reporting Officer (Author) or Command Staff can edit a report.
    - Once a report is linked to a Case, it might be locked (optional business logic),
      but generally, authors correct their own reports.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if hasattr(obj, 'reporting_officer') and obj.reporting_officer == request.user:
            return True

        return False
