from django.db import models
from django.conf import settings
from django.utils import timezone

class Case(models.Model):
    class CrimeLevel(models.IntegerChoices):
        CRITICAL = 4, 'Critical'
        LEVEL_1 = 3, 'Level 1 (High)'
        LEVEL_2 = 2, 'Level 2 (Medium)'
        LEVEL_3 = 1, 'Level 3 (Low)'

    class CaseStatus(models.TextChoices):
        PENDING_APPROVAL = 'PENDING', 'Pending Approval'
        OPEN = 'OPEN', 'Open for Investigation'
        INVESTIGATION_COMPLETE = 'INVEST_DONE', 'Investigation Complete'
        AWAITING_TRIAL = 'AWAITING_TRIAL', 'Awaiting Trial'
        CLOSED_CONVICTION = 'CLOSED_GUILTY', 'Closed (Conviction)'
        CLOSED_ACQUITTAL = 'CLOSED_NOT_GUILTY', 'Closed (Acquittal)'
        CLOSED_COLD = 'CLOSED_COLD', 'Closed (Cold Case)'
        REJECTED = 'REJECTED', 'Rejected'

    title = models.CharField(max_length=255, verbose_name="Case Title")
    description = models.TextField(verbose_name="Case Summary Description")
    crime_level = models.IntegerField(choices=CrimeLevel.choices, verbose_name="Crime Level")
    status = models.CharField(max_length=20, choices=CaseStatus.choices, default=CaseStatus.PENDING_APPROVAL)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Key Personnel
    lead_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="led_cases",
        # Limit choices in Django admin/forms to users with an access level of 40+
        # limit_choices_to={'roles__access_level__gte': 40}
    )
    assigned_personnel = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_cases",
        blank=True
    )

    complainants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='filed_cases',
        blank=True,
        verbose_name="Complainants"
    )
    
    # Involved Parties (Civilians)
    suspects = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='CaseSuspect',
        related_name="suspected_in_cases",
        blank=True,
        through_fields=('case', 'suspect') 
    )

    def __str__(self):
        return f"CASE-{self.id:05d}: {self.title}"

class Complaint(models.Model):
    class Status(models.TextChoices):
        PENDING_CADET = 'PENDING_CADET', 'Pending Cadet Review'
        PENDING_OFFICER = 'PENDING_OFFICER', 'Pending Officer Review'
        RETURNED_TO_COMPLAINANT = 'RETURNED_TO_COMPLAINANT', 'Returned to Complainant (Defect)'
        RETURNED_TO_CADET = 'RETURNED_TO_CADET', 'Returned to Cadet (Defect)'
        APPROVED = 'APPROVED', 'Approved (Case Created/Joined)'
        ARCHIVED = 'ARCHIVED', 'Archived (Nullified - 3 Strikes)'


    cadet_message = models.TextField(verbose_name="Cadet's Rejection Message", blank=True, null=True)
    complainant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    details = models.TextField(verbose_name="Complaint Details")
    status = models.CharField(max_length=200, choices=Status.choices, default=Status.PENDING_CADET)
    rejection_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Once approved, this links to the official Case
    target_case = models.ForeignKey(
        Case, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='linked_complaints',
        help_text="If this complaint belongs to an existing case, link it here."
    )

    def __str__(self):
        return f"Complaint by {self.complainant.username} on {self.created_at.strftime('%Y-%m-%d')}"

class CrimeSceneReport(models.Model):
    class Status(models.TextChoices):
        PENDING_SUPERIOR = 'PENDING_SUPERIOR', 'Pending Superior Approval'
        APPROVED = 'APPROVED', 'Approved (Case Created)'
        REJECTED = 'REJECTED', 'Rejected'

    reporting_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='crime_reports',
        limit_choices_to={'role__access_level__gte': 20} # Officer or higher
    )
    scene_datetime = models.DateTimeField()
    location_details = models.CharField(max_length=255)
    report_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING_SUPERIOR)
    
    # Once approved, this links to the official Case
    case = models.OneToOneField(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='originating_report')

    def __str__(self):
        return f"Report by {self.reporting_officer.username} for scene at {self.scene_datetime.strftime('%Y-%m-%d')}"

class CaseSuspect(models.Model):
    class Status(models.TextChoices):
        # Initial Stages
        WANTED = 'WANTED', 'Wanted'
        HIGHLY_WANTED = 'HIGHLY_WANTED', 'Highly Wanted (Critical)'
        
        # Arrest & Investigation (Chapter 4.5)
        IN_CUSTODY = 'IN_CUSTODY', 'In Custody (Interrogation Pending)'
        PENDING_SERGEANT_REVIEW = 'PENDING_SGT', 'Pending Sergeant Review'
        
        # Outcomes of Investigation
        RELEASED_INSUFFICIENT_EVIDENCE = 'RELEASED_EVIDENCE', 'Released (Insufficient Evidence)'
        SENT_TO_TRIAL = 'SENT_TO_TRIAL', 'Sent to Trial'
        
        # Logistics (Chapter 4.9)
        RELEASED_ON_BAIL = 'BAIL', 'Released on Bail'
        
        # Trial Outcomes (Chapter 4.6)
        CONVICTED = 'CONVICTED', 'Convicted'
        ACQUITTED = 'ACQUITTED', 'Acquitted'

    case = models.ForeignKey('Case', on_delete=models.CASCADE)
    suspect = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.WANTED)
    
    # Tracking Dates (For Chapter 4.7 Formula)
    date_marked_wanted = models.DateTimeField(auto_now_add=True)
    date_arrested = models.DateTimeField(null=True, blank=True)
    
    # Interrogation Data (Chapter 4.5)
    detective_notes = models.TextField(blank=True, help_text="Interrogation summary by Lead Detective")
    detective_score = models.PositiveIntegerField(default=0, help_text="Guilt probability score (1-10)")
    
    sergeant_notes = models.TextField(blank=True, help_text="Review notes by Sergeant")
    sergeant_score = models.PositiveIntegerField(default=0, help_text="Validation score (1-10)")
    
    # Hierarchy Approval (For Critical Crimes)
    captain_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        related_name='captain_approvals'
    )
    chief_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        related_name='chief_approvals'
    )

    class Meta:
        unique_together = ('case', 'suspect')
        verbose_name_plural = "Case Suspects"

    def __str__(self):
        return f"{self.suspect.username} - {self.get_status_display()}"

    @property
    def days_wanted(self):
        """Calculates D_i for Chapter 4.7 Most Wanted Formula"""
        if self.status not in [self.Status.WANTED, self.Status.HIGHLY_WANTED]:
            return 0
        delta = timezone.now() - self.date_marked_wanted
        return delta.days