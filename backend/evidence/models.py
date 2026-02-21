from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class EvidenceBase(models.Model):
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class WitnessEvidence(EvidenceBase):
    transcript = models.TextField(blank=True)
    media_url = models.URLField(blank=True)


class BiologicalEvidence(EvidenceBase):
    image_urls = models.JSONField(default=list, blank=True)
    forensic_result = models.TextField(blank=True)
    identity_db_result = models.TextField(blank=True)


class VehicleEvidence(EvidenceBase):
    model_name = models.CharField(max_length=120)
    color = models.CharField(max_length=60)
    plate_number = models.CharField(max_length=30, blank=True)
    serial_number = models.CharField(max_length=60, blank=True)

    def clean(self):
        if bool(self.plate_number) == bool(self.serial_number):
            raise ValidationError('Exactly one of plate_number or serial_number must be set.')


class IdentificationEvidence(EvidenceBase):
    owner_full_name = models.CharField(max_length=120)
    metadata = models.JSONField(default=dict, blank=True)


class OtherEvidence(EvidenceBase):
    pass
