from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BailPaymentViewSet, payment_return_page

router = DefaultRouter()
router.register('bail', BailPaymentViewSet, basename='bail')

urlpatterns = router.urls + [
    path('return/', payment_return_page),
]
