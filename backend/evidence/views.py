from rest_framework import decorators, permissions, status, viewsets
from rest_framework.response import Response

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
        if request.user.is_superuser:
            return
        if getattr(self, 'action', None) == 'update_results' and user_has_action(request.user, 'evidence.biological.review'):
            return
        if not user_has_action(request.user, 'evidence.manage'):
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

    @decorators.action(detail=True, methods=['post'])
    def update_results(self, request, pk=None):
        obj = self.get_object()
        allowed = (
            request.user.is_superuser
            or user_has_action(request.user, 'evidence.biological.review')
        )
        if not allowed:
            return Response({'detail': 'No permission'}, status=status.HTTP_403_FORBIDDEN)

        forensic_result = request.data.get('forensic_result', obj.forensic_result)
        identity_db_result = request.data.get('identity_db_result', obj.identity_db_result)
        obj.forensic_result = forensic_result
        obj.identity_db_result = identity_db_result
        obj.save(update_fields=['forensic_result', 'identity_db_result'])
        return Response(self.get_serializer(obj).data)


class VehicleEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = VehicleEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = VehicleEvidenceSerializer


class IdentificationEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = IdentificationEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = IdentificationEvidenceSerializer


class OtherEvidenceViewSet(RecordedByMixin, viewsets.ModelViewSet):
    queryset = OtherEvidence.objects.select_related('case', 'recorded_by').all()
    serializer_class = OtherEvidenceSerializer
