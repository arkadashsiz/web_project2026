from django.contrib import admin
from .models import WitnessEvidence, BiologicalEvidence, VehicleEvidence, IdentificationEvidence, OtherEvidence

admin.site.register(WitnessEvidence)
admin.site.register(BiologicalEvidence)
admin.site.register(VehicleEvidence)
admin.site.register(IdentificationEvidence)
admin.site.register(OtherEvidence)
