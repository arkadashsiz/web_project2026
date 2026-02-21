# investigation/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DetectiveBoardViewSet,
    InvestigationWorkflowViewSet,
    TrialViewSet,
    MostWantedViewSet
)

# ایجاد یک روتر پیش‌فرض برای ثبت ViewSet ها
router = DefaultRouter()

# ثبت مسیر بورد کارآگاهان
# مثال: GET /api/investigations/boards/ | POST /api/investigations/boards/
router.register(r'boards', DetectiveBoardViewSet, basename='detective-board')

# ثبت مسیرهای ورک‌فلو بازجویی و تاییدات (روی CaseSuspect کار می‌کند)
# مثال: POST /api/investigations/workflow/{id}/request_arrest_warrant/
# مثال: POST /api/investigations/workflow/{id}/submit_interrogation/
router.register(r'workflow', InvestigationWorkflowViewSet, basename='investigation-workflow')

# ثبت مسیرهای دادگاه (روی CaseSuspect کار می‌کند)
# مثال: POST /api/investigations/trials/{id}/submit_verdict/
router.register(r'trials', TrialViewSet, basename='trial')

# ثبت مسیر لیست تحت تعقیب (فقط خواندنی)
# مثال: GET /api/investigations/most-wanted/
router.register(r'most-wanted', MostWantedViewSet, basename='most-wanted')

urlpatterns = [
    # شامل کردن تمام مسیرهای ساخته شده توسط روتر
    path('', include(router.urls)),
]
