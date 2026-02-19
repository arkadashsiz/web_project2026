from rest_framework import viewsets, generics, permissions, filters
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView

# Internal app imports
from .models import Role
from .serializers import (
    RoleSerializer, 
    UserSerializer, 
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer
)
from .permissions import IsCommandStaff, IsAccountOwner, IsSuperUser

User = get_user_model()

# ==========================================
# AUTHENTICATION & REGISTRATION VIEWS
# ==========================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Login View.
    Authenticates the user and returns a JWT containing the user's
    role, access level, and basic profile info embedded in the payload.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    """
    Public endpoint for registering new civilian users.
    Automatically assigns the 'Civilian' role via the serializer.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


# ==========================================
# USER & ROLE MANAGEMENT VIEWS
# ==========================================

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing User profiles.
    - Civilians: Can only see and edit their own profile.
    - Police (Access Level >= 10): Can search and view all users.
    - Command Staff: Can edit anyone or delete users.
    """
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', 'first_name', 'last_name', 'national_id', 'phone_number']
    filterset_fields = ['role__name']

    def get_queryset(self):
        user = self.request.user
        
        # If user is police (Access Level >= 10), they can search and see all users
        if user.role and user.role.access_level >= 10:
            return User.objects.all()
            
        # Civilians can only see their own account
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.action == 'create':
            # Creation is handled by UserRegistrationView. 
            # If hit here directly, require Command Staff.
            return [IsSuperUser()]
        
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Users can edit themselves OR Command Staff can edit anyone
            return [IsAccountOwner() , IsSuperUser()]
            
        # List and Retrieve require standard authentication
        return [permissions.IsAuthenticated()]


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Roles.
    - Read-only for all authenticated users.
    - Create/Update/Delete restricted STRICTLY to Superusers.
    """
    queryset = Role.objects.all().order_by('access_level')
    serializer_class = RoleSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['access_level', 'name']

    def get_permissions(self):
        # STRICT: Only Superuser can modify roles structure
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperUser()]
            
        # Anyone logged in can view the roles (e.g., for dropdown menus)
        return [permissions.IsAuthenticated()]
