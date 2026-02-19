from rest_framework import permissions
from users.permissions import IsCommandStaff

class IsCaseReadOnlyIfClosed(permissions.BasePermission):
    """
    Prevents modification of Cases that are marked as CLOSED, ARCHIVED, or REJECTED.
    Only Command Staff (Captain/Chief) can reopen/edit a closed case.
    """
    def has_object_permission(self, request, view, obj):
        # 1. Read permissions are allowed to any authorized user (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. Command Staff (Level >= 80) can override and edit closed cases
        if IsCommandStaff().has_permission(request, view):
            return True

        # 3. Define Closed/Locked Statuses based on models.py
        # Note: We access the choices from the instance class or directly as strings
        locked_statuses = [
            'CLOSED_GUILTY', 
            'CLOSED_NOT_GUILTY', 
            'CLOSED_COLD', 
            'REJECTED'
        ]

        # 4. If the case status is locked, deny write access
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
        # Read permissions are allowed to any Police Personnel (checked by view)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Command Staff override
        if IsCommandStaff().has_permission(request, view):
            return True

        # Check if user is the assigned Lead Detective
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
        # 1. Check if user is Police
        is_police = False
        if request.user.role and request.user.role.access_level >= 10:
            is_police = True

        # 2. READ Access
        if request.method in permissions.SAFE_METHODS:
            if is_police:
                return True
            # Civilian: Must be the complainant
            return obj.complainant == request.user

        # 3. WRITE Access (Edit/Delete)
        if is_police:
            # Police can edit (usually to change status), logic handled in Serializer/View validation
            return True
        
        # Civilian: Can only edit if they own it AND it is still Pending
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

        # Command Staff override
        if IsCommandStaff().has_permission(request, view):
            return True

        # Author check
        if hasattr(obj, 'reporting_officer') and obj.reporting_officer == request.user:
            return True

        return False
