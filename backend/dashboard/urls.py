from django.urls import path
from .views import stats, modules

urlpatterns = [
    path('stats/', stats),
    path('modules/', modules),
]
