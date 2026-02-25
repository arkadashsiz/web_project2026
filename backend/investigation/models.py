from django.conf import settings
from django.db import models
from django.utils import timezone


class DetectiveBoard(models.Model):
    case = models.OneToOneField('cases.Case', on_delete=models.CASCADE, related_name='board')
    detective = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    exported_image_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class BoardNode(models.Model):
    class Kind(models.TextChoices):
        NOTE = 'note', 'Note'
        EVIDENCE = 'evidence', 'Evidence'
        SUSPECT = 'suspect', 'Suspect'

    board = models.ForeignKey(DetectiveBoard, on_delete=models.CASCADE, related_name='nodes')
    label = models.CharField(max_length=150)
    x = models.FloatField(default=50)
    y = models.FloatField(default=50)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.NOTE)
    reference_id = models.PositiveIntegerField(null=True, blank=True)


class BoardEdge(models.Model):
    board = models.ForeignKey(DetectiveBoard, on_delete=models.CASCADE, related_name='edges')
    from_node = models.ForeignKey(BoardNode, on_delete=models.CASCADE, related_name='out_edges')
    to_node = models.ForeignKey(BoardNode, on_delete=models.CASCADE, related_name='in_edges')
    reason = models.CharField(max_length=255, blank=True)


class Suspect(models.Model):
    class Status(models.TextChoices):
        WANTED = 'wanted', 'Wanted'
        HIGH_ALERT = 'high_alert', 'High Alert'
        ARRESTED = 'arrested', 'Arrested'
        CLEARED = 'cleared', 'Cleared'
        CRIMINAL = 'criminal', 'Criminal'

    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='suspects')
    person = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    full_name = models.CharField(max_length=120)
    national_id = models.CharField(max_length=20, blank=True)
    photo_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WANTED)
    marked_at = models.DateTimeField(default=timezone.now)

    def days_wanted(self):
        return (timezone.now() - self.marked_at).days


class Interrogation(models.Model):
    class CaptainDecision(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUBMITTED = 'submitted', 'Submitted'

    class CaptainOutcome(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved To Trial'
        REJECTED = 'rejected', 'Rejected'

    class ChiefDecision(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        NOT_REQUIRED = 'not_required', 'Not Required'

    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='interrogations')
    suspect = models.ForeignKey(Suspect, on_delete=models.CASCADE, related_name='interrogations')
    detective = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='detective_interrogations')
    sergeant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sergeant_interrogations')
    transcription = models.TextField(blank=True)
    key_values = models.JSONField(default=dict, blank=True)
    detective_note = models.TextField(blank=True)
    sergeant_note = models.TextField(blank=True)
    detective_score = models.PositiveSmallIntegerField(default=1)
    sergeant_score = models.PositiveSmallIntegerField(default=1)
    detective_submitted = models.BooleanField(default=False)
    sergeant_submitted = models.BooleanField(default=False)
    captain_score = models.PositiveSmallIntegerField(null=True, blank=True)
    captain_note = models.TextField(blank=True)
    captain_decision = models.CharField(max_length=20, choices=CaptainDecision.choices, default=CaptainDecision.PENDING)
    captain_outcome = models.CharField(max_length=20, choices=CaptainOutcome.choices, default=CaptainOutcome.PENDING)
    captain_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='captain_interrogation_reviews'
    )
    captain_decided_at = models.DateTimeField(null=True, blank=True)
    chief_decision = models.CharField(max_length=20, choices=ChiefDecision.choices, default=ChiefDecision.NOT_REQUIRED)
    chief_note = models.TextField(blank=True)
    chief_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chief_interrogation_reviews'
    )
    chief_decided_at = models.DateTimeField(null=True, blank=True)
    chief_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class SuspectSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='suspect_submissions')
    detective = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='detective_submissions')
    suspects = models.ManyToManyField(Suspect, related_name='submissions')
    detective_reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    sergeant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sergeant_reviews'
    )
    sergeant_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
