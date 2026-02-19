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
        # 1. Read permissions are always allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. Command Staff Override
        if IsCommandStaff().has_permission(request, view):
            return True

        # 3. Resolve the 'case' object based on the model type
        case_obj = None
        
        # For DetectiveBoard and Trial, 'case' is a direct field
        if hasattr(obj, 'case'):
            case_obj = obj.case
        # For Interrogation, it is linked via 'case_suspect'
        elif hasattr(obj, 'case_suspect'):
            case_obj = obj.case_suspect.case

        # 4. Check status
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
        # Read-only for authenticated users (checked by view)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Command Staff Override
        if IsCommandStaff().has_permission(request, view):
            return True

        # Check if user is the Lead Detective of the associated case
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

        # 1. Check Command Staff (Captains/Chiefs need access to approve)
        if IsCommandStaff().has_permission(request, view):
            return True

        # 2. Check Interrogators
        # The Sergeant conducting it
        if obj.interrogating_sergeant == request.user:
            return True
        
        # The Detective assisting
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
        # Allow Safe Methods (Police need to see the verdict)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write access requires the user to be a Judge (Level 70)
        # We check the role level first for efficiency
        if request.user.role and request.user.role.access_level == 70:
            return True
            
        # Admin override (optional, for data correction)
        if request.user.is_superuser:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only the specific Judge assigned to this trial can edit it.
        if obj.judge == request.user:
            return True
            
        return False
