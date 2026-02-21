from django.contrib import admin
from .models import Case, ComplaintSubmission, CaseComplainant, CaseWitness, CaseLog

admin.site.register(Case)
admin.site.register(ComplaintSubmission)
admin.site.register(CaseComplainant)
admin.site.register(CaseWitness)
admin.site.register(CaseLog)
