from django.conf import settings
from django.db import models


class BailPayment(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'initiated', 'Initiated'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE)
    suspect = models.ForeignKey('investigation.Suspect', on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    # For level 3 criminals, sergeant must explicitly approve release-by-payment.
    sergeant_approved = models.BooleanField(default=False)
    authority = models.CharField(max_length=64, blank=True)
    gateway_status = models.CharField(max_length=50, blank=True)
    payment_ref = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
