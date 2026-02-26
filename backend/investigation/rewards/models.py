from django.conf import settings
from django.db import models
import uuid


class Tip(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        REJECTED = 'rejected', 'Rejected'
        SENT_TO_DETECTIVE = 'sent_to_detective', 'Sent To Detective'
        APPROVED = 'approved', 'Approved'

    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, null=True, blank=True)
    suspect = models.ForeignKey('investigation.Suspect', on_delete=models.CASCADE, null=True, blank=True)
    assigned_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tips',
    )
    content = models.TextField()
    officer_note = models.TextField(blank=True)
    detective_note = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)


class RewardClaim(models.Model):
    tip = models.OneToOneField(Tip, on_delete=models.CASCADE, related_name='claim')
    unique_code = models.CharField(max_length=40, unique=True, default='')
    amount = models.BigIntegerField(default=0)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    is_paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.unique_code:
            self.unique_code = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)
