from rest_framework import decorators, permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from cases.models import Case
from cases.serializers import CaseSerializer, CaseLogSerializer
from evidence.models import WitnessEvidence, BiologicalEvidence, VehicleEvidence, IdentificationEvidence, OtherEvidence
from evidence.serializers import (
    WitnessEvidenceSerializer,
    BiologicalEvidenceSerializer,
    VehicleEvidenceSerializer,
    IdentificationEvidenceSerializer,
    OtherEvidenceSerializer,
)
from investigation.models import Suspect
from investigation.serializers import SuspectSerializer, InterrogationSerializer, SuspectSubmissionSerializer
from rbac.permissions import user_has_action
from .models import CourtSession
from .serializers import CourtSessionSerializer


class CourtSessionViewSet(viewsets.ModelViewSet):
    queryset = CourtSession.objects.select_related('case', 'judge').all()
    serializer_class = CourtSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not (request.user.is_superuser or user_has_action(request.user, 'judiciary.verdict')):
            self.permission_denied(request, message='No permission')

    @decorators.action(detail=False, methods=['get'])
    def case_summary(self, request):
        case_id = request.query_params.get('case_id')
        if not case_id:
            return Response({'detail': 'case_id is required'}, status=400)

        case = Case.objects.filter(id=case_id).select_related('created_by', 'assigned_detective').first()
        if not case:
            return Response({'detail': 'Case not found'}, status=404)

        suspects = Suspect.objects.filter(case=case)
        interrogations = case.interrogations.select_related(
            'detective', 'sergeant', 'captain_by', 'chief_by', 'suspect'
        ).all()
        submissions = case.suspect_submissions.select_related('detective', 'sergeant').prefetch_related('suspects').all()

        involved_users = {}
        for u in [case.created_by, case.assigned_detective]:
            if u:
                involved_users[u.id] = u
        for log in case.logs.select_related('actor').all():
            involved_users[log.actor_id] = log.actor
        for i in interrogations:
            for u in [i.detective, i.sergeant, i.captain_by, i.chief_by]:
                if u:
                    involved_users[u.id] = u
        for s in submissions:
            for u in [s.detective, s.sergeant]:
                if u:
                    involved_users[u.id] = u

        def user_row(u):
            return {
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'national_id': u.national_id,
                'roles': list(u.user_roles.values_list('role__name', flat=True)),
            }

        payload = {
            'case': CaseSerializer(case).data,
            'evidence': {
                'witness': WitnessEvidenceSerializer(WitnessEvidence.objects.filter(case=case), many=True).data,
                'biological': BiologicalEvidenceSerializer(BiologicalEvidence.objects.filter(case=case), many=True).data,
                'vehicle': VehicleEvidenceSerializer(VehicleEvidence.objects.filter(case=case), many=True).data,
                'identification': IdentificationEvidenceSerializer(IdentificationEvidence.objects.filter(case=case), many=True).data,
                'other': OtherEvidenceSerializer(OtherEvidence.objects.filter(case=case), many=True).data,
            },
            'suspects': SuspectSerializer(suspects, many=True).data,
            'interrogations': InterrogationSerializer(interrogations, many=True).data,
            'suspect_submissions': SuspectSubmissionSerializer(submissions, many=True).data,
            'logs': CaseLogSerializer(case.logs.all(), many=True).data,
            'involved_members': [user_row(u) for u in involved_users.values()],
            'court_session': CourtSessionSerializer(case.court_session).data if hasattr(case, 'court_session') else None,
        }
        return Response(payload)

    def perform_create(self, serializer):
        case = serializer.validated_data['case']
        if case.status != Case.Status.SENT_TO_COURT:
            raise PermissionDenied('Case must be in sent_to_court status before trial.')
        session = serializer.save(judge=self.request.user)
        case = session.case
        case.status = Case.Status.CLOSED
        case.save(update_fields=['status', 'updated_at'])

        suspects = Suspect.objects.filter(case=case)
        if session.verdict == CourtSession.Verdict.GUILTY:
            suspects.update(status=Suspect.Status.CRIMINAL)
        else:
            suspects.update(status=Suspect.Status.CLEARED)
