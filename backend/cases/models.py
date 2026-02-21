from django.conf import settings
from django.db import models


class Case(models.Model):
    class Source(models.TextChoices):
        COMPLAINT = 'complaint', 'Complaint'
        SCENE = 'scene', 'Scene Report'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        UNDER_REVIEW = 'under_review', 'Under Review'
        OPEN = 'open', 'Open'
        INVESTIGATING = 'investigating', 'Investigating'
        SENT_TO_COURT = 'sent_to_court', 'Sent To Court'
        CLOSED = 'closed', 'Closed'
        VOID = 'void', 'Void'

    class Severity(models.IntegerChoices):
        LEVEL_3 = 1, 'Level 3'
        LEVEL_2 = 2, 'Level 2'
        LEVEL_1 = 3, 'Level 1'
        CRITICAL = 4, 'Critical'

    title = models.CharField(max_length=255)
    description = models.TextField()
    source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    severity = models.IntegerField(choices=Severity.choices, default=Severity.LEVEL_3)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_cases')
    assigned_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='detective_cases'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Case#{self.id} - {self.title}'


class ComplaintSubmission(models.Model):
    class Stage(models.TextChoices):
        TO_CADET = 'to_cadet', 'To Cadet'
        TO_OFFICER = 'to_officer', 'To Officer'
        RETURNED_TO_COMPLAINANT = 'returned_to_complainant', 'Returned To Complainant'
        RETURNED_TO_CADET = 'returned_to_cadet', 'Returned To Cadet'
        FORMED = 'formed', 'Formed'
        VOIDED = 'voided', 'Voided'

    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='complaint_submission')
    complainant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    stage = models.CharField(max_length=30, choices=Stage.choices, default=Stage.TO_CADET)
    intern_note = models.TextField(blank=True)
    officer_note = models.TextField(blank=True)
    last_error_message = models.TextField(blank=True)


class CaseComplainant(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='complainants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    review_note = models.TextField(blank=True)

    class Meta:
        unique_together = ('case', 'user')


class CaseWitness(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='witnesses')
    full_name = models.CharField(max_length=120)
    national_id = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    statement = models.TextField(blank=True)


class CaseLog(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=120)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
