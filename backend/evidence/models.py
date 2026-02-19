# evidence/models.py

from django.db import models
from django.conf import settings

class Evidence(models.Model):
    class EvidenceType(models.TextChoices):
        TESTIMONY = 'TESTIMONY', 'Witness Testimony'
        BIOLOGICAL = 'BIOLOGICAL', 'Biological/Medical'
        VEHICLE = 'VEHICLE', 'Vehicle'
        ID_DOCUMENT = 'ID_DOCUMENT', 'ID Document'
        OTHER = 'OTHER', 'Other'

    # Note the string notation 'cases.Case' to link across apps
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='evidence')
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_collected = models.DateTimeField()
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='collected_evidence')
    evidence_type = models.CharField(max_length=20, choices=EvidenceType.choices)

    def __str__(self):
        return f"{self.get_evidence_type_display()}: {self.title} for {self.case}"

class Testimony(models.Model):
    evidence_ptr = models.OneToOneField(Evidence, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    witness = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='testimonies')
    transcription = models.TextField()
    media_file = models.FileField(upload_to='evidence/testimony/', null=True, blank=True)

class Biological(models.Model):
    evidence_ptr = models.OneToOneField(Evidence, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    image = models.ImageField(upload_to='evidence/biological/', null=True, blank=True)
    coroner_report = models.TextField(blank=True, help_text="Findings from the coroner.")
    identity_bank_result = models.TextField(blank=True, help_text="Results from the identity bank query.")

class Vehicle(models.Model):
    evidence_ptr = models.OneToOneField(Evidence, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=20, null=True, blank=True)
    serial_number = models.CharField(max_length=50, null=True, blank=True, help_text="VIN or other serial number")

class IDDocument(models.Model):
    evidence_ptr = models.OneToOneField(Evidence, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    document_type = models.CharField(max_length=100, help_text="e.g., Driver's License, Passport")
    owner_full_name = models.CharField(max_length=255)
    additional_info = models.JSONField(default=dict, blank=True, help_text="Key-value pairs of document data.")
