from rest_framework import permissions
from users.permissions import IsCommandStaff

class IsInvestigationActive(permissions.BasePermission):
    """
    Prevents modification of Investigation data (Boards, Interrogations) 
    if the parent Case is CLOSED/ARCHIVED.
    
    This ensures that once a case is adjudicated or went cold, 
    the investigation notes cannot be tampered with retroactively.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        case_obj = None
        
        if hasattr(obj, 'case'):
            case_obj = obj.case
        elif hasattr(obj, 'case_suspect'):
            case_obj = obj.case_suspect.case

        if case_obj:
            locked_statuses = [
                'CLOSED_GUILTY', 
                'CLOSED_NOT_GUILTY', 
                'CLOSED_COLD', 
                'REJECTED'
            ]
            if case_obj.status in locked_statuses:
                return False

        return True


class IsBoardOwnerOrCommand(permissions.BasePermission):
    """
    Permissions for the DetectiveBoard.
    - Only the Lead Detective of the Case can edit the board.
    - Command Staff can edit/override.
    - Other officers have Read-Only access.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if hasattr(obj, 'case') and obj.case.lead_detective == request.user:
            return True

        return False


class IsInterrogationParticipantOrCommand(permissions.BasePermission):
    """
    Permissions for Interrogation records.
    - Allows Edit access to:
        1. The Interrogating Sergeant.
        2. The Assisting Detective.
        3. The Captain (Approver).
        4. The Chief (Final Approver).
    
    Note: Field-level security (e.g., ensuring the Sergeant cannot change the 
    Captain's approval status) must be handled in the Serializer `validate` method. 
    This permission simply grants access to the object.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if IsCommandStaff().has_permission(request, view):
            return True

        if obj.interrogating_sergeant == request.user:
            return True
        
        if obj.assisting_detective == request.user:
            return True

        return False


class IsJudgeForTrial(permissions.BasePermission):
    """
    Permissions for the Trial model.
    - Strictly limits Write/Edit access to the assigned Judge.
    - Police cannot edit Trial records (Separation of Powers).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user.role and request.user.role.access_level == 70:
            return True
            
        if request.user.is_superuser:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if obj.judge == request.user:
            return True
            
        return False
