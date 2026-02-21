from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

if settings.HAS_SPECTACULAR:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/rbac/', include('rbac.urls')),
    path('api/cases/', include('cases.urls')),
    path('api/evidence/', include('evidence.urls')),
    path('api/investigation/', include('investigation.urls')),
    path('api/judiciary/', include('judiciary.urls')),
    path('api/rewards/', include('rewards.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/dashboard/', include('dashboard.urls')),
]

if settings.HAS_SPECTACULAR:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
