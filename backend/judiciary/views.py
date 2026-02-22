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
    queryset = CourtSession.objects.select_related('case', 'judge', 'convicted_suspect').all()
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
            'complainant_details': [
                {
                    'id': row.id,
                    'status': row.status,
                    'review_note': row.review_note,
                    'user': user_row(row.user),
                }
                for row in case.complainants.select_related('user').all()
            ],
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
            'court_sessions': CourtSessionSerializer(case.court_sessions.order_by('-id'), many=True).data,
        }
        return Response(payload)

    def perform_create(self, serializer):
        case = serializer.validated_data['case']
        if case.status not in [Case.Status.SENT_TO_COURT]:
            raise PermissionDenied('Case must be in sent_to_court status before trial verdict.')
        convicted_suspect = serializer.validated_data.get('convicted_suspect')
        verdict = serializer.validated_data.get('verdict')
        if not convicted_suspect:
            raise PermissionDenied('convicted_suspect is required.')
        if convicted_suspect.case_id != case.id:
            raise PermissionDenied('convicted_suspect must belong to this case.')
        session = serializer.save(judge=self.request.user)

        if session.verdict == CourtSession.Verdict.GUILTY:
            convicted_suspect.status = Suspect.Status.CRIMINAL
            convicted_suspect.save(update_fields=['status'])
        else:
            convicted_suspect.status = Suspect.Status.CLEARED
            convicted_suspect.save(update_fields=['status'])

        total_suspects = Suspect.objects.filter(case=case).count()
        finalized_suspects = CourtSession.objects.filter(case=case).values('convicted_suspect_id').distinct().count()
        if total_suspects == 0 or finalized_suspects >= total_suspects:
            case.status = Case.Status.CLOSED
            case.save(update_fields=['status', 'updated_at'])
