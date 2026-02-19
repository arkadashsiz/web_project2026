import uuid
from django.db import models
from django.conf import settings

class Tip(models.Model):
    class Status(models.TextChoices):
        PENDING_REVIEW = 'PENDING', 'Pending Review'
        USEFUL = 'USEFUL', 'Marked as Useful'
        REWARDED = 'REWARDED', 'Reward Claimed'
        REJECTED = 'REJECTED', 'Rejected'

    informant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tips')
    # Note the string notation 'cases.Case'
    case = models.ForeignKey('cases.Case', on_delete=models.SET_NULL, null=True, blank=True, help_text="The case this tip relates to.")
    information = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_REVIEW)
    unique_reward_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reward_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, help_text="Amount in Rials.")
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    class PaymentType(models.TextChoices):
        BAIL = 'BAIL', 'Bail'
        FINE = 'FINE', 'Fine'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESSFUL = 'SUCCESS', 'Successful'
        FAILED = 'FAILED', 'Failed'
    
    # Note the string notation 'cases.CaseSuspect'
    case_suspect = models.ForeignKey('cases.CaseSuspect', on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=10, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=0) # In Rials
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
