# investigation/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


# --- Detective Board Models (Chapter 4.4) ---

class DetectiveBoard(models.Model):
    case = models.OneToOneField('cases.Case', on_delete=models.CASCADE, related_name='detective_board')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Board for Case {self.case_id}"


class BoardItem(models.Model):
    board = models.ForeignKey(DetectiveBoard, on_delete=models.CASCADE, related_name='items')
    # Requires evidence app and Evidence model
    evidence = models.ForeignKey('evidence.Evidence', on_delete=models.CASCADE, related_name='board_placements')
    x_position = models.FloatField(default=0.0)
    y_position = models.FloatField(default=0.0)

    def __str__(self):
        return f"Item {self.evidence_id} at ({self.x_position}, {self.y_position})"


class BoardConnection(models.Model):
    board = models.ForeignKey(DetectiveBoard, on_delete=models.CASCADE, related_name='connections')
    from_item = models.ForeignKey(BoardItem, on_delete=models.CASCADE, related_name='outgoing_connections')
    to_item = models.ForeignKey(BoardItem, on_delete=models.CASCADE, related_name='incoming_connections')
    color = models.CharField(max_length=20, default='red')  # "Red Thread"

    def __str__(self):
        return f"Connection from {self.from_item_id} to {self.to_item_id}"


# --- Interrogation Workflow Model (Chapter 4.5) ---

class Interrogation(models.Model):
    case_suspect = models.OneToOneField('cases.CaseSuspect', on_delete=models.CASCADE, related_name='interrogation')

    # Detective
    detective = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='detective_interrogations')
    detective_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)
    detective_notes = models.TextField(blank=True)

    # Sergeant
    sergeant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sergeant_interrogations')
    sergeant_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)
    sergeant_notes = models.TextField(blank=True)

    # Approvals
    captain_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='captain_approvals')
    chief_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chief_approvals')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Interrogation: {self.case_suspect_id}"

    def is_fully_evaluated(self):
        # both scores present and valid (1..10 enforced by validators)
        return self.detective_score is not None and self.sergeant_score is not None


# --- Judicial/Trial Model (Chapter 4.6) ---

class Trial(models.Model):
    VERDICT_CHOICES = [
        ('GUILTY', 'Guilty'),
        ('NOT_GUILTY', 'Not Guilty'),
        ('MISTRIAL', 'Mistrial'),
    ]

    case_suspect = models.OneToOneField('cases.CaseSuspect', on_delete=models.CASCADE, related_name='trial')
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES)
    sentence_years = models.IntegerField(default=0, help_text="Prison sentence in years (if guilty)")
    judge_notes = models.TextField(blank=True)
    trial_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Trial for {self.case_suspect_id} - {self.verdict}"
