from rest_framework import viewsets, generics, permissions, filters
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action

# Internal app imports
from .models import Role
from .serializers import (
    RoleSerializer, 
    UserSerializer, 
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer
)
from .permissions import (
    IsCommandStaff, 
    IsAccountOwner, 
    IsSuperUser, 
    IsAccountOwnerOrSuperUser, 
    IsAccountOwnerOrCommand
)

User = get_user_model()

# ==========================================
# AUTHENTICATION & REGISTRATION VIEWS
# ==========================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Login View.
    Authenticates the user and returns a JWT containing the user's
    roles list, access level, and basic profile info embedded in the payload.
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
    - Police: Can search and view all users.
    - Command Staff / Superuser: Can edit anyone or delete users.
    """
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', 'first_name', 'last_name', 'national_id', 'phone_number']
    
    # UPDATED: Changed from 'role__name' to 'roles__name' to support ManyToMany relation
    filterset_fields = ['roles__name']

    def get_queryset(self):
        user = self.request.user
        
        if not bool(user and user.is_authenticated):
            return User.objects.none()
            
        # UPDATED: Replaced the singular role check with our new is_police property
        # If user is police or superuser, they can search and see all users
        if user.is_police or user.is_superuser:
            return User.objects.all()
            
        # Civilians can only see their own account
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.action == 'create':
            # Creation is handled by UserRegistrationView. 
            # If hit here directly via the API, require Superuser.
            return [IsSuperUser()]
        
        elif self.action in ['update', 'partial_update', 'destroy']:
            # UPDATED: Applied IsAccountOwnerOrCommand to match your docstring logic.
            # Users can edit themselves OR Command Staff/Superusers can edit anyone.
            return [IsAccountOwnerOrCommand()]
            
        # List and Retrieve require standard authentication
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperUser], url_path='grant-role')
    def grant_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get('role_id')

        if not role_id:
            return Response(
                {"detail": "role_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        user.roles.add(role)

        return Response(
            {
                "detail": f"Role '{role.name}' granted to {user.username}.",
                "user_id": user.id,
                "role_id": role.id
            },
            status=status.HTTP_200_OK
        )


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
            
        # Anyone logged in can view the roles (e.g., for dropdown menus on the frontend)
        return [permissions.IsAuthenticated()]
    
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
    
from .models import RoleRequest
from .serializers import RoleRequestSerializer, ProcessRoleRequestSerializer
from .permissions import IsSuperUser

class RoleRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RoleRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return RoleRequest.objects.all()
        return RoleRequest.objects.filter(user=user)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Modifying requests is not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Deleting requests is not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
