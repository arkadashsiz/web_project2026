from rest_framework import permissions, viewsets

from investigation.models import Notification
from rbac.permissions import user_has_action
from .models import WitnessEvidence, BiologicalEvidence, VehicleEvidence, IdentificationEvidence, OtherEvidence
from .serializers import (
    WitnessEvidenceSerializer,
    BiologicalEvidenceSerializer,
    VehicleEvidenceSerializer,
    IdentificationEvidenceSerializer,
    OtherEvidenceSerializer,
)


class EvidencePermissionMixin:
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not (request.user.is_superuser or user_has_action(request.user, 'evidence.manage')):
            self.permission_denied(request, message='No permission')


class RecordedByMixin(EvidencePermissionMixin):
    def perform_create(self, serializer):
        obj = serializer.save(recorded_by=self.request.user)
        detective = getattr(obj.case, 'assigned_detective', None)
        if detective:
            Notification.objects.create(
                recipient=detective,
                case=obj.case,
                message=f'New evidence added: {obj.title}',
            )


class WitnessEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = WitnessEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = WitnessEvidenceSerializer


class BiologicalEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = BiologicalEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = BiologicalEvidenceSerializer


class VehicleEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = VehicleEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = VehicleEvidenceSerializer


class IdentificationEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = IdentificationEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = IdentificationEvidenceSerializer


class OtherEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = OtherEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = OtherEvidenceSerializer
