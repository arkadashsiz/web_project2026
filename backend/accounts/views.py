from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from rest_framework_simplejwt.tokens import RefreshToken
except Exception:
    RefreshToken = None

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('identifier')
        password = request.data.get('password')
        if not identifier or not password:
            return Response({'detail': 'identifier and password are required'}, status=400)

        user = User.objects.filter(
            Q(username=identifier) | Q(email=identifier) | Q(phone=identifier) | Q(national_id=identifier)
        ).first()

        if not user or not user.check_password(password):
            return Response({'detail': 'Invalid credentials'}, status=401)

        if RefreshToken is None:
            return Response({'detail': 'simplejwt package is not installed in this environment'}, status=501)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        })


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        if not self.request.user.is_superuser:
            return User.objects.none()
        return User.objects.all().order_by('id')
