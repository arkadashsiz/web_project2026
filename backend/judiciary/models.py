from django.conf import settings
from django.db import models


class CourtSession(models.Model):
    class Verdict(models.TextChoices):
        GUILTY = 'guilty', 'Guilty'
        NOT_GUILTY = 'not_guilty', 'Not Guilty'

    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='court_sessions')
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    verdict = models.CharField(max_length=20, choices=Verdict.choices)
    convicted_suspect = models.ForeignKey(
        'investigation.Suspect',
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='court_verdicts',
    )
    punishment_title = models.CharField(max_length=255, blank=True)
    punishment_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('case', 'convicted_suspect')
