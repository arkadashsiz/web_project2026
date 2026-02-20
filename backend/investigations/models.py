from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class EvidenceConnection(models.Model):
    """
    Represents the 'Detective Board'. 
    It connects a specific piece of Evidence to a specific Suspect within a Case.
    """
    class ConnectionStrength(models.TextChoices):
        CIRCUMSTANTIAL = 'CIRCUMSTANTIAL', 'Circumstantial'
        CORROBORATING = 'CORROBORATING', 'Corroborating'
        DIRECT = 'DIRECT', 'Direct Link'

    # Links
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='board_connections')
    suspect = models.ForeignKey('cases.CaseSuspect', on_delete=models.CASCADE, related_name='evidence_links')
    evidence = models.ForeignKey('evidence.Evidence', on_delete=models.CASCADE, related_name='suspect_connections')
    
    # Metadata
    strength = models.CharField(max_length=20, choices=ConnectionStrength.choices, default=ConnectionStrength.CIRCUMSTANTIAL)
    notes = models.TextField(blank=True, help_text="Detective's notes on how this evidence connects to the suspect.")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('suspect', 'evidence') # One piece of evidence can't be linked to the same suspect twice

    def __str__(self):
        return f"Link: {self.evidence.title} -> {self.suspect}"

class Trial(models.Model):
    """
    Represents the Judicial phase. Only accessible by Judges.
    """
    class Verdict(models.TextChoices):
        GUILTY = 'GUILTY', 'Guilty'
        NOT_GUILTY = 'NOT_GUILTY', 'Not Guilty'
        MISTRIAL = 'MISTRIAL', 'Mistrial'

    # One trial per CaseSuspect entry
    case_suspect = models.OneToOneField('cases.CaseSuspect', on_delete=models.CASCADE, related_name='trial')
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='trials_judged')
    
    date_started = models.DateField()
    date_concluded = models.DateField(null=True, blank=True)
    
    verdict = models.CharField(max_length=20, choices=Verdict.choices, null=True, blank=True)
    sentence_years = models.IntegerField(default=0, help_text="0 if not guilty or suspended")
    
    court_transcripts = models.TextField(blank=True)
    
    def clean(self):
        # Ensure the user is actually a judge (Level 70)
        if self.judge.access_level < 70:
            raise ValidationError("The assigned user is not a Judge.")

    def __str__(self):
        return f"Trial for {self.case_suspect} - Judge {self.judge.last_name}"
