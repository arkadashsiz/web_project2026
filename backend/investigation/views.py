from collections import defaultdict

from django.utils import timezone
from rest_framework import decorators, permissions, status, viewsets
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
from rbac.permissions import user_has_action
from .models import DetectiveBoard, BoardNode, BoardEdge, Suspect, Interrogation, Notification
from .serializers import (
    DetectiveBoardSerializer,
    BoardNodeSerializer,
    BoardEdgeSerializer,
    SuspectSerializer,
    InterrogationSerializer,
    NotificationSerializer,
)


def require_action(user, action):
    return user.is_superuser or user_has_action(user, action)


class DetectiveBoardViewSet(viewsets.ModelViewSet):
    queryset = DetectiveBoard.objects.select_related('case', 'detective').all()
    serializer_class = DetectiveBoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not require_action(request.user, 'investigation.board.manage'):
            self.permission_denied(request, message='No permission')

    def _sync_board_nodes(self, board, case):
        existing_keys = set(
            board.nodes.values_list('kind', 'reference_id', 'label')
        )

        # Layout counters for new nodes only.
        x = 80
        y = 80

        def add_if_missing(kind, ref_id, label, px, py):
            key = (kind, ref_id, label)
            if key in existing_keys:
                return
            BoardNode.objects.create(
                board=board,
                label=label,
                kind=kind,
                reference_id=ref_id,
                x=px,
                y=py,
            )
            existing_keys.add(key)

        suspects = Suspect.objects.filter(case=case)
        witness_evidence = WitnessEvidence.objects.filter(case=case)
        biological_evidence = BiologicalEvidence.objects.filter(case=case)
        vehicle_evidence = VehicleEvidence.objects.filter(case=case)
        identification_evidence = IdentificationEvidence.objects.filter(case=case)
        other_evidence = OtherEvidence.objects.filter(case=case)

        for s in suspects:
            add_if_missing(BoardNode.Kind.SUSPECT, s.id, f'Suspect: {s.full_name}', x, y)
            x += 180

        def add_evidence_nodes(rows, prefix):
            nonlocal x
            for row in rows:
                add_if_missing(BoardNode.Kind.EVIDENCE, row.id, f'{prefix}: {row.title}', x, y + 150)
                x += 180

        add_evidence_nodes(witness_evidence, 'Witness')
        add_evidence_nodes(biological_evidence, 'Biological')
        add_evidence_nodes(vehicle_evidence, 'Vehicle')
        add_evidence_nodes(identification_evidence, 'Identification')
        add_evidence_nodes(other_evidence, 'Other')

    @decorators.action(detail=False, methods=['post'])
    def open_case_board(self, request):
        case_id = request.data.get('case_id')
        if not case_id:
            return Response({'detail': 'case_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        case = Case.objects.filter(id=case_id).select_related('assigned_detective', 'created_by').first()
        if not case:
            return Response({'detail': 'Case not found'}, status=status.HTTP_404_NOT_FOUND)

        can_access = (
            request.user.is_superuser
            or user_has_action(request.user, 'case.read_all')
            or case.assigned_detective_id == request.user.id
        )
        if not can_access:
            return Response({'detail': 'Only assigned detective can open this board'}, status=status.HTTP_403_FORBIDDEN)

        board, _ = DetectiveBoard.objects.get_or_create(case=case, defaults={'detective': request.user})
        if board.detective_id != request.user.id and (request.user.is_superuser or case.assigned_detective_id == request.user.id):
            board.detective = request.user
            board.save(update_fields=['detective', 'updated_at'])

        # Sync missing suspect/evidence cards every time board is opened.
        self._sync_board_nodes(board, case)

        context = {
            'board': DetectiveBoardSerializer(board).data,
            'case': CaseSerializer(case).data,
            'suspects': SuspectSerializer(Suspect.objects.filter(case=case), many=True).data,
            'evidence': {
                'witness': WitnessEvidenceSerializer(WitnessEvidence.objects.filter(case=case), many=True).data,
                'biological': BiologicalEvidenceSerializer(BiologicalEvidence.objects.filter(case=case), many=True).data,
                'vehicle': VehicleEvidenceSerializer(VehicleEvidence.objects.filter(case=case), many=True).data,
                'identification': IdentificationEvidenceSerializer(IdentificationEvidence.objects.filter(case=case), many=True).data,
                'other': OtherEvidenceSerializer(OtherEvidence.objects.filter(case=case), many=True).data,
            },
            'logs': CaseLogSerializer(case.logs.all(), many=True).data,
        }
        return Response(context)


class BoardNodeViewSet(viewsets.ModelViewSet):
    queryset = BoardNode.objects.select_related('board').all()
    serializer_class = BoardNodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not require_action(request.user, 'investigation.board.manage'):
            self.permission_denied(request, message='No permission')


class BoardEdgeViewSet(viewsets.ModelViewSet):
    queryset = BoardEdge.objects.select_related('board', 'from_node', 'to_node').all()
    serializer_class = BoardEdgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not require_action(request.user, 'investigation.board.manage'):
            self.permission_denied(request, message='No permission')


class SuspectViewSet(viewsets.ModelViewSet):
    queryset = Suspect.objects.select_related('case').all()
    serializer_class = SuspectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not require_action(request.user, 'suspect.manage'):
            self.permission_denied(request, message='No permission')

    @decorators.action(detail=True, methods=['post'])
    def arrest(self, request, pk=None):
        suspect = self.get_object()
        suspect.status = Suspect.Status.ARRESTED
        suspect.save(update_fields=['status'])
        return Response(self.get_serializer(suspect).data)


class InterrogationViewSet(viewsets.ModelViewSet):
    queryset = Interrogation.objects.select_related('case', 'suspect', 'detective', 'sergeant').all()
    serializer_class = InterrogationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action in ['captain_decision']:
            ok = require_action(request.user, 'interrogation.captain_decision')
        elif self.action in ['chief_review']:
            ok = require_action(request.user, 'interrogation.chief_review')
        else:
            ok = require_action(request.user, 'interrogation.manage')
        if not ok:
            self.permission_denied(request, message='No permission')

    @decorators.action(detail=True, methods=['post'])
    def captain_decision(self, request, pk=None):
        obj = self.get_object()
        obj.captain_score = request.data.get('captain_score')
        obj.captain_note = request.data.get('captain_note', '')
        obj.save(update_fields=['captain_score', 'captain_note'])

        if obj.case.severity == Case.Severity.CRITICAL:
            chiefs = obj.case.created_by.__class__.objects.filter(user_roles__role__name='chief').distinct()
            for chief in chiefs:
                Notification.objects.create(
                    recipient=chief,
                    case=obj.case,
                    message='Critical case captain decision requires chief review.',
                )
        return Response(self.get_serializer(obj).data)

    @decorators.action(detail=True, methods=['post'])
    def chief_review(self, request, pk=None):
        obj = self.get_object()
        obj.chief_reviewed = True
        obj.save(update_fields=['chief_reviewed'])
        return Response(self.get_serializer(obj).data)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @decorators.action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'status': 'ok'})


@decorators.api_view(['GET'])
@decorators.permission_classes([permissions.IsAuthenticated])
def high_alert_list(request):
    suspects = Suspect.objects.select_related('case').all()

    grouped = defaultdict(list)
    for s in suspects:
        key = s.national_id.strip() or f'case-{s.case_id}-suspect-{s.id}'
        grouped[key].append(s)

    out = []
    for key, items in grouped.items():
        max_lj = 0
        max_di = 0
        representative = items[0]

        for s in items:
            if s.case.status != Case.Status.CLOSED:
                max_lj = max(max_lj, max(s.days_wanted(), 0))
            max_di = max(max_di, s.case.severity)

        rank_score = max_lj * max_di
        reward = rank_score * 20_000_000
        is_high_alert = max_lj > 30

        for s in items:
            new_status = Suspect.Status.HIGH_ALERT if is_high_alert else s.status
            if s.status != new_status:
                s.status = new_status
                s.save(update_fields=['status'])

        if is_high_alert:
            out.append({
                'group_key': key,
                'suspect_id': representative.id,
                'full_name': representative.full_name,
                'national_id': representative.national_id,
                'photo_url': representative.photo_url,
                'max_lj_days': max_lj,
                'max_di': max_di,
                'rank_score': rank_score,
                'reward_irr': reward,
            })

    out.sort(key=lambda x: x['rank_score'], reverse=True)
    return Response(out)
