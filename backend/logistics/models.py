from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
import uuid

# Import Case/Suspect from the cases app
from cases.models import Case, CaseSuspect

class CivilianTip(models.Model):
    class Status(models.TextChoices):
        PENDING_OFFICER = 'PENDING_OFFICER', 'Pending Officer Review'
        PENDING_DETECTIVE = 'PENDING_DETECTIVE', 'Pending Detective Review'
        APPROVED = 'APPROVED', 'Approved (Reward Generated)'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_tips')
    
    # The tip can be about a specific Case OR a specific Suspect (User)
    related_case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True)
    related_suspect = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tips_against')
    
    content = models.TextField(help_text="Details provided by the civilian")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_OFFICER)
    
    # Review Logs
    officer_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_tips_officer')
    detective_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_tips_detective')
    
    # Reward Logic (Chapter 4.8)
    unique_token = models.CharField(max_length=12, unique=True, null=True, blank=True)
    reward_amount = models.BigIntegerField(default=0, help_text="Amount in Rials")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_token(self):
        """Generates a unique 10-char token for the user to claim reward."""
        if not self.unique_token:
            self.unique_token = get_random_string(10).upper()
            self.save()

    def __str__(self):
        return f"Tip {self.id} by {self.user.username} - {self.status}"


class BailTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Payment'
        PAID = 'PAID', 'Paid/Verified'
        FAILED = 'FAILED', 'Failed'

    case_suspect = models.ForeignKey(CaseSuspect, on_delete=models.CASCADE, related_name='bail_transactions')
    amount = models.BigIntegerField(help_text="Amount in Rials")
    description = models.CharField(max_length=255)
    
    # Zarinpal Fields
    authority = models.CharField(max_length=100, blank=True, null=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Bail for {self.case_suspect.suspect.username}: {self.amount} Rials"
