from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class DetectiveBoard(models.Model):
    # Note the string notation 'cases.Case'
    case = models.OneToOneField('cases.Case', on_delete=models.CASCADE, related_name='detective_board')
    board_data = models.JSONField(default=dict, blank=True, help_text="Stores positions of evidence, links, and notes.")
    last_updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    last_updated_at = models.DateTimeField(auto_now=True)

class Interrogation(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    # Note the string notation 'cases.CaseSuspect'
    case_suspect = models.ForeignKey('cases.CaseSuspect', on_delete=models.CASCADE, related_name='interrogations')
    interrogating_sergeant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='sergeant_interrogations',
        limit_choices_to={'roles__access_level__gte': 60}
    )
    assisting_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='detective_interrogations',
        limit_choices_to={'roles__access_level__gte': 40}
    )
    
    sergeant_guilt_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    detective_guilt_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    captain_approval = models.CharField(max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    captain_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='captain_approvals',
        limit_choices_to={'roles__access_level__gte': 80}
    )
    
    # For critical crimes only
    chief_approval = models.CharField(max_length=10, choices=ApprovalStatus.choices, null=True, blank=True)
    chief_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='chief_approvals',
        limit_choices_to={'roles__access_level__gte': 100}
    )

    interrogation_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

class Trial(models.Model):
    """Represents the final trial and verdict by a judge."""
    class Verdict(models.TextChoices):
        GUILTY = 'GUILTY', 'Guilty'
        NOT_GUILTY = 'NOT_GUILTY', 'Not Guilty'

    # Note the string notation 'cases.Case'
    case = models.OneToOneField('cases.Case', on_delete=models.PROTECT, related_name='trial')
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='judged_trials',
        limit_choices_to={'roles__name': 'Judge'}
    )
    verdict = models.CharField(max_length=15, choices=Verdict.choices)
    punishment_details = models.TextField(blank=True, help_text="Sentence or other punishment details, if guilty.")
    trial_date = models.DateField()
