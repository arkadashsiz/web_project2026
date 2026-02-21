from django.urls import path
from django.http import JsonResponse
from .views import RegisterView, LoginView, MeView, UserListView

try:
    from rest_framework_simplejwt.views import TokenRefreshView
except Exception:
    def token_refresh_fallback(request):
        return JsonResponse({'detail': 'simplejwt is not installed in this environment'}, status=501)

    class TokenRefreshView:
        @staticmethod
        def as_view():
            return token_refresh_fallback

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('refresh/', TokenRefreshView.as_view()),
    path('me/', MeView.as_view()),
    path('users/', UserListView.as_view()),
]
