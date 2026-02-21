from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q


class Evidence(models.Model):
    class EvidenceType(models.TextChoices):
        TESTIMONY = 'TESTIMONY', 'Witness Testimony'
        BIOLOGICAL = 'BIOLOGICAL', 'Biological/Medical'
        VEHICLE = 'VEHICLE', 'Vehicle'
        ID_DOCUMENT = 'ID_DOCUMENT', 'ID Document'
        OTHER = 'OTHER', 'Other'

    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='evidence')
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_collected = models.DateTimeField(default=timezone.now)
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='collected_evidence')
    evidence_type = models.CharField(max_length=20, choices=EvidenceType.choices)

    class Meta:
        ordering = ['-date_collected']

    def __str__(self):
        return f"{self.get_evidence_type_display()}: {self.title} for {self.case}"


class Testimony(Evidence):
    witness = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='testimonies')
    transcription = models.TextField()
    media_file = models.FileField(upload_to='evidence/testimony/', null=True, blank=True)


class Biological(Evidence):
    image = models.ImageField(upload_to='evidence/biological/', null=True, blank=True)
    coroner_report = models.TextField(blank=True, help_text="Findings from the coroner.")
    identity_bank_result = models.TextField(blank=True, help_text="Results from the identity bank query.")


class Vehicle(Evidence):
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=20, null=True, blank=True)
    serial_number = models.CharField(max_length=50, null=True, blank=True, help_text="VIN or other serial number")

    def clean(self):
        if self.license_plate == "":
            self.license_plate = None
        if self.serial_number == "":
            self.serial_number = None

        if self.license_plate and self.serial_number:
            raise ValueError("A vehicle cannot have both a license plate and a serial number.")
        if not self.license_plate and not self.serial_number:
            raise ValueError("You must provide either a license plate or a serial number.")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(license_plate__isnull=False) & Q(serial_number__isnull=True)) |
                    (Q(license_plate__isnull=True) & Q(serial_number__isnull=False))
                ),
                name="vehicle_plate_xor_serial"
            )
        ]


class IDDocument(Evidence):
    document_type = models.CharField(max_length=100, help_text="e.g., Driver's License, Passport")
    owner_full_name = models.CharField(max_length=255)
    additional_info = models.JSONField(default=dict, blank=True, help_text="Key-value pairs of document data.")

class WitnessStatement(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='witness_statements')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='witness_statements')
    statement = models.TextField()
    media_file = models.FileField(upload_to='statements/', null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_statements')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Statement by {self.submitted_by} for Case {self.case_id}"
