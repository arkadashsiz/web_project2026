from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserViewSet, 
    RoleViewSet, 
    UserRegistrationView, 
    CustomTokenObtainPairView,
    RoleRequestViewSet
)

# Initialize the DefaultRouter for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'role-requests', RoleRequestViewSet, basename='role-request')

urlpatterns = [
    # ==========================================
    # AUTHENTICATION ENDPOINTS (JWT)
    # ==========================================
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ==========================================
    # REGISTRATION ENDPOINT
    # ==========================================
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    
    # ==========================================
    # USER & ROLE MANAGEMENT ENDPOINTS
    # ==========================================
    # This includes:
    # GET /users/ (List users)
    # POST /users/ (Create user - restricted)
    # GET /users/<id>/ (Retrieve specific user)
    # PUT/PATCH /users/<id>/ (Update user)
    # DELETE /users/<id>/ (Delete user)
    # GET /roles/ (List roles)
    # ... and other role endpoints
    path('', include(router.urls)),
]
