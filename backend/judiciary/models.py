from django.conf import settings
from django.db import models


class CourtSession(models.Model):
    class Verdict(models.TextChoices):
        GUILTY = 'guilty', 'Guilty'
        NOT_GUILTY = 'not_guilty', 'Not Guilty'

    case = models.OneToOneField('cases.Case', on_delete=models.CASCADE, related_name='court_session')
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    verdict = models.CharField(max_length=20, choices=Verdict.choices)
    punishment_title = models.CharField(max_length=255, blank=True)
    punishment_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
