from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db.models import Q
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
from .models import DetectiveBoard, BoardNode, BoardEdge, Suspect, Interrogation, Notification, SuspectSubmission
from .serializers import (
    DetectiveBoardSerializer,
    BoardNodeSerializer,
    BoardEdgeSerializer,
    SuspectSerializer,
    InterrogationSerializer,
    NotificationSerializer,
    SuspectSubmissionSerializer,
)

User = get_user_model()


def require_action(user, action):
    return user.is_superuser or user_has_action(user, action)


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


class DetectiveBoardViewSet(viewsets.ModelViewSet):
    queryset = DetectiveBoard.objects.select_related('case', 'detective').all()
    serializer_class = DetectiveBoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action == 'open_case_board':
            ok = (
                require_action(request.user, 'investigation.board.manage')
                or require_action(request.user, 'suspect.manage')
                or require_action(request.user, 'case.read_all')
            )
            if not ok:
                self.permission_denied(request, message='No permission')
        else:
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

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset.select_related('board__case')
        if user.is_superuser or require_action(user, 'case.read_all'):
            return qs
        return qs.filter(board__case__assigned_detective=user)

    def check_permissions(self, request):
        super().check_permissions(request)
        if not require_action(request.user, 'investigation.board.manage'):
            self.permission_denied(request, message='No permission')

    def perform_create(self, serializer):
        board = serializer.validated_data.get('board')
        if not board:
            self.permission_denied(self.request, message='board is required')
        if not self.request.user.is_superuser and board.case.assigned_detective_id != self.request.user.id:
            self.permission_denied(self.request, message='Only assigned detective can modify board')
        serializer.save()


class BoardEdgeViewSet(viewsets.ModelViewSet):
    queryset = BoardEdge.objects.select_related('board', 'from_node', 'to_node').all()
    serializer_class = BoardEdgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset.select_related('board__case', 'from_node', 'to_node')
        if user.is_superuser or require_action(user, 'case.read_all'):
            return qs
        return qs.filter(board__case__assigned_detective=user)

    def check_permissions(self, request):
        super().check_permissions(request)
        if not require_action(request.user, 'investigation.board.manage'):
            self.permission_denied(request, message='No permission')

    def perform_create(self, serializer):
        board = serializer.validated_data.get('board')
        if not board:
            self.permission_denied(self.request, message='board is required')
        if not self.request.user.is_superuser and board.case.assigned_detective_id != self.request.user.id:
            self.permission_denied(self.request, message='Only assigned detective can modify board')
        serializer.save()


class SuspectViewSet(viewsets.ModelViewSet):
    queryset = Suspect.objects.select_related('case').all()
    serializer_class = SuspectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.is_superuser or require_action(user, 'case.read_all'):
            return qs
        return qs.filter(
            Q(case__assigned_detective=user)
            | Q(case__suspect_submissions__sergeant=user, case__suspect_submissions__status=SuspectSubmission.Status.APPROVED)
        ).distinct()

    def check_permissions(self, request):
        super().check_permissions(request)
        if not require_action(request.user, 'suspect.manage'):
            self.permission_denied(request, message='No permission')

    def perform_create(self, serializer):
        case = serializer.validated_data.get('case')
        if not case:
            self.permission_denied(self.request, message='case is required')
        if not self.request.user.is_superuser and case.assigned_detective_id != self.request.user.id:
            self.permission_denied(self.request, message='Only assigned detective can add suspects to this case')
        serializer.save()

    def perform_update(self, serializer):
        suspect = self.get_object()
        if not self.request.user.is_superuser and suspect.case.assigned_detective_id != self.request.user.id:
            self.permission_denied(self.request, message='Only assigned detective can edit suspects')
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_superuser and instance.case.assigned_detective_id != self.request.user.id:
            self.permission_denied(self.request, message='Only assigned detective can delete suspects')
        instance.delete()

    @decorators.action(detail=True, methods=['post'])
    def arrest(self, request, pk=None):
        suspect = self.get_object()
        if not request.user.is_superuser:
            is_assigned_detective = suspect.case.assigned_detective_id == request.user.id
            is_case_sergeant = SuspectSubmission.objects.filter(
                case=suspect.case,
                status=SuspectSubmission.Status.APPROVED,
                sergeant=request.user,
                suspects=suspect,
            ).exists()
            if not (is_assigned_detective or is_case_sergeant):
                return Response({'detail': 'Only case detective or case sergeant reviewer can arrest'}, status=403)
        suspect.status = Suspect.Status.ARRESTED
        suspect.save(update_fields=['status'])
        return Response(self.get_serializer(suspect).data)


class InterrogationViewSet(viewsets.ModelViewSet):
    queryset = Interrogation.objects.select_related('case', 'suspect', 'detective', 'sergeant').all()
    serializer_class = InterrogationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        user = self.request.user
        if (
            user.is_superuser
            or require_action(user, 'case.read_all')
            or require_action(user, 'interrogation.captain_decision')
            or require_action(user, 'interrogation.chief_review')
        ):
            return qs.order_by('-id')
        return qs.filter(Q(detective=user) | Q(sergeant=user)).order_by('-id')

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action in ['captain_decision']:
            ok = require_action(request.user, 'interrogation.captain_decision')
        elif self.action in ['chief_review']:
            ok = require_action(request.user, 'interrogation.chief_review')
        elif self.action in ['create', 'update', 'partial_update', 'destroy', 'record_assessment']:
            ok = require_action(request.user, 'interrogation.manage')
        else:
            ok = (
                require_action(request.user, 'interrogation.manage')
                or require_action(request.user, 'interrogation.captain_decision')
                or require_action(request.user, 'interrogation.chief_review')
                or require_action(request.user, 'case.read_all')
            )
        if not ok:
            self.permission_denied(request, message='No permission')

    @decorators.action(detail=False, methods=['post'])
    def record_assessment(self, request):
        case_id = request.data.get('case_id')
        suspect_id = request.data.get('suspect_id')
        if not case_id or not suspect_id:
            return Response({'detail': 'case_id and suspect_id are required.'}, status=400)

        case = Case.objects.filter(id=case_id).first()
        suspect = Suspect.objects.filter(id=suspect_id, case_id=case_id).first()
        if not case or not suspect:
            return Response({'detail': 'Case/suspect combination not found.'}, status=404)
        if suspect.status != Suspect.Status.ARRESTED:
            return Response({'detail': 'Interrogation is allowed only for arrested suspects.'}, status=400)

        interrogation = Interrogation.objects.filter(case=case, suspect=suspect).first()
        if not interrogation:
            interrogation = Interrogation.objects.create(
                case=case,
                suspect=suspect,
                detective=case.assigned_detective or request.user,
                sergeant=request.user,
                chief_decision=(
                    Interrogation.ChiefDecision.PENDING
                    if case.severity == Case.Severity.CRITICAL
                    else Interrogation.ChiefDecision.NOT_REQUIRED
                ),
            )

        changed_fields = []
        wants_detective_update = any(k in request.data for k in ['detective_score', 'detective_note'])
        wants_sergeant_update = any(k in request.data for k in ['sergeant_score', 'sergeant_note'])
        if 'transcription' in request.data:
            interrogation.transcription = request.data.get('transcription', '') or ''
            changed_fields.append('transcription')
        if 'key_values' in request.data:
            kv = request.data.get('key_values', {})
            if kv in [None, '']:
                kv = {}
            if not isinstance(kv, dict):
                return Response({'detail': 'key_values must be an object/dictionary.'}, status=400)
            interrogation.key_values = kv
            changed_fields.append('key_values')

        # Only the assigned detective of this case can set detective scoring.
        if wants_detective_update:
            if not require_action(request.user, 'investigation.board.manage'):
                return Response({'detail': 'No permission for detective scoring.'}, status=403)
            is_case_detective = (
                case.assigned_detective_id == request.user.id
                or interrogation.detective_id == request.user.id
            )
            if not request.user.is_superuser and not is_case_detective:
                return Response({'detail': 'Only assigned detective for this case can score.'}, status=403)
            if 'detective_score' in request.data and request.data.get('detective_score') is not None:
                ds = int(request.data.get('detective_score'))
                if ds < 1 or ds > 10:
                    return Response({'detail': 'detective_score must be between 1 and 10.'}, status=400)
                interrogation.detective_score = ds
                changed_fields.append('detective_score')
            if 'detective_note' in request.data:
                interrogation.detective_note = request.data.get('detective_note', '') or ''
                changed_fields.append('detective_note')
            if interrogation.detective_id != request.user.id and request.user == case.assigned_detective:
                interrogation.detective = request.user
                changed_fields.append('detective')

        # Only the sergeant who reviewed/approved main suspects for this case can set sergeant scoring.
        if wants_sergeant_update:
            if not require_action(request.user, 'suspect.manage'):
                return Response({'detail': 'No permission for sergeant scoring.'}, status=403)
            approved_submission = SuspectSubmission.objects.filter(
                case=case,
                status=SuspectSubmission.Status.APPROVED,
                sergeant=request.user,
                suspects=suspect,
            ).exists()
            is_case_sergeant = (
                interrogation.sergeant_id == request.user.id
                or approved_submission
            )
            if not request.user.is_superuser and not is_case_sergeant:
                return Response({'detail': 'Only case sergeant reviewer can score.'}, status=403)
            if 'sergeant_score' in request.data and request.data.get('sergeant_score') is not None:
                ss = int(request.data.get('sergeant_score'))
                if ss < 1 or ss > 10:
                    return Response({'detail': 'sergeant_score must be between 1 and 10.'}, status=400)
                interrogation.sergeant_score = ss
                changed_fields.append('sergeant_score')
            if 'sergeant_note' in request.data:
                interrogation.sergeant_note = request.data.get('sergeant_note', '') or ''
                changed_fields.append('sergeant_note')
            if interrogation.sergeant_id != request.user.id:
                interrogation.sergeant = request.user
                changed_fields.append('sergeant')

        if changed_fields:
            interrogation.save(update_fields=list(set(changed_fields)))

        # Notify captains after both detective/sergeant scores are available.
        if (
            interrogation.detective_score is not None
            and interrogation.sergeant_score is not None
            and interrogation.captain_decision == Interrogation.CaptainDecision.PENDING
        ):
            captains = User.objects.filter(user_roles__role__permissions__action='interrogation.captain_decision').distinct()
            for captain in captains:
                Notification.objects.create(
                    recipient=captain,
                    case=case,
                    message=f'Interrogation scores are ready for case #{case.id} suspect #{suspect.id}. Captain decision required.',
                )

        return Response(self.get_serializer(interrogation).data)

    @decorators.action(detail=True, methods=['post'])
    def captain_decision(self, request, pk=None):
        obj = self.get_object()
        approved_raw = request.data.get('approved', None)
        if approved_raw is None:
            return Response({'detail': 'approved is required (true/false)'}, status=400)
        approved = parse_bool(approved_raw, default=False)
        score = request.data.get('captain_score')
        note = (request.data.get('captain_note') or '').strip()
        if score is None:
            return Response({'detail': 'captain_score is required'}, status=400)
        score = int(score)
        if score < 1 or score > 10:
            return Response({'detail': 'captain_score must be between 1 and 10'}, status=400)
        if not note:
            return Response({'detail': 'captain_note is required'}, status=400)

        obj.captain_score = score
        obj.captain_note = note
        obj.captain_decision = Interrogation.CaptainDecision.SUBMITTED
        obj.captain_outcome = Interrogation.CaptainOutcome.APPROVED if approved else Interrogation.CaptainOutcome.REJECTED
        obj.captain_by = request.user
        obj.captain_decided_at = timezone.now()

        if not approved:
            obj.chief_decision = Interrogation.ChiefDecision.NOT_REQUIRED
            obj.case.status = Case.Status.INVESTIGATING
            obj.case.save(update_fields=['status', 'updated_at'])
            for recipient in [obj.detective, obj.sergeant]:
                Notification.objects.create(
                    recipient=recipient,
                    case=obj.case,
                    message=f'Captain rejected interrogation #{obj.id} for trial. Continue investigation.',
                )
        elif obj.case.severity == Case.Severity.CRITICAL:
            obj.chief_decision = Interrogation.ChiefDecision.PENDING
            chiefs = User.objects.filter(user_roles__role__permissions__action='interrogation.chief_review').distinct()
            for chief in chiefs:
                Notification.objects.create(
                    recipient=chief,
                    case=obj.case,
                    message=f'Critical case #{obj.case.id} interrogation #{obj.id} needs chief review.',
                )
        else:
            obj.chief_decision = Interrogation.ChiefDecision.NOT_REQUIRED
            obj.case.status = Case.Status.SENT_TO_COURT
            obj.case.save(update_fields=['status', 'updated_at'])
            for recipient in [obj.detective, obj.sergeant]:
                Notification.objects.create(
                    recipient=recipient,
                    case=obj.case,
                    message=f'Captain finalized interrogation #{obj.id}. Case sent to court.',
                )

        obj.save(update_fields=[
            'captain_score', 'captain_note', 'captain_decision', 'captain_outcome', 'captain_by',
            'captain_decided_at', 'chief_decision',
        ])
        return Response(self.get_serializer(obj).data)

    @decorators.action(detail=True, methods=['post'])
    def chief_review(self, request, pk=None):
        obj = self.get_object()
        if obj.case.severity != Case.Severity.CRITICAL:
            return Response({'detail': 'Chief review is only for critical cases.'}, status=400)
        if obj.captain_decision != Interrogation.CaptainDecision.SUBMITTED:
            return Response({'detail': 'Captain decision must be submitted first.'}, status=400)
        if obj.captain_outcome != Interrogation.CaptainOutcome.APPROVED:
            return Response({'detail': 'Chief review is available only when captain approved trial.'}, status=400)

        approved_raw = request.data.get('approved', None)
        if approved_raw is None:
            return Response({'detail': 'approved is required (true/false).'}, status=400)
        approved = parse_bool(approved_raw, default=False)
        note = (request.data.get('chief_note') or '').strip()

        obj.chief_decision = Interrogation.ChiefDecision.APPROVED if approved else Interrogation.ChiefDecision.REJECTED
        obj.chief_note = note
        obj.chief_reviewed = True
        obj.chief_by = request.user
        obj.chief_decided_at = timezone.now()
        obj.save(update_fields=['chief_decision', 'chief_note', 'chief_reviewed', 'chief_by', 'chief_decided_at'])

        if approved:
            obj.case.status = Case.Status.SENT_TO_COURT
            obj.case.save(update_fields=['status', 'updated_at'])

        if obj.captain_by:
            Notification.objects.create(
                recipient=obj.captain_by,
                case=obj.case,
                message=f'Chief {"approved" if approved else "rejected"} captain decision for interrogation #{obj.id}.',
            )
        for recipient in [obj.detective, obj.sergeant]:
            Notification.objects.create(
                recipient=recipient,
                case=obj.case,
                message=f'Chief {"approved" if approved else "rejected"} interrogation #{obj.id} decision.',
            )
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


class SuspectSubmissionViewSet(viewsets.ModelViewSet):
    queryset = SuspectSubmission.objects.select_related('case', 'detective', 'sergeant').prefetch_related('suspects').all()
    serializer_class = SuspectSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        case_id = self.request.query_params.get('case_id')
        if case_id:
            qs = qs.filter(case_id=case_id)

        user = self.request.user
        if user.is_superuser or require_action(user, 'case.read_all'):
            return qs
        if require_action(user, 'suspect.manage'):
            return qs.filter(Q(status=SuspectSubmission.Status.PENDING) | Q(sergeant=user)).distinct()
        return qs.filter(detective=user)

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action == 'submit_main_suspects':
            ok = require_action(request.user, 'investigation.board.manage')
        elif self.action == 'sergeant_review':
            ok = require_action(request.user, 'suspect.manage')
        else:
            ok = request.user.is_authenticated
        if not ok:
            self.permission_denied(request, message='No permission')

    @decorators.action(detail=False, methods=['post'])
    def submit_main_suspects(self, request):
        case_id = request.data.get('case_id')
        suspect_ids = request.data.get('suspect_ids', [])
        reason = (request.data.get('detective_reason') or '').strip()

        if not case_id or not isinstance(suspect_ids, list) or len(suspect_ids) == 0 or not reason:
            return Response({'detail': 'case_id, suspect_ids, detective_reason are required.'}, status=400)

        case = Case.objects.filter(id=case_id).first()
        if not case:
            return Response({'detail': 'Case not found'}, status=404)
        if not request.user.is_superuser and case.assigned_detective_id != request.user.id:
            return Response({'detail': 'Only assigned detective can submit main suspects.'}, status=403)

        suspects = Suspect.objects.filter(case=case, id__in=suspect_ids)
        if suspects.count() != len(set(suspect_ids)):
            return Response({'detail': 'Some suspects do not belong to this case.'}, status=400)

        submission = SuspectSubmission.objects.create(
            case=case,
            detective=request.user,
            detective_reason=reason,
            status=SuspectSubmission.Status.PENDING,
        )
        submission.suspects.set(suspects)

        sergeants = User.objects.filter(user_roles__role__permissions__action='suspect.manage').distinct()
        for sg in sergeants:
            Notification.objects.create(
                recipient=sg,
                case=case,
                message=f'Detective submitted main suspects for case #{case.id}. Please review.',
            )

        return Response(SuspectSubmissionSerializer(submission).data, status=201)

    @decorators.action(detail=True, methods=['post'])
    def sergeant_review(self, request, pk=None):
        submission = self.get_object()
        if submission.status != SuspectSubmission.Status.PENDING:
            return Response({'detail': 'Submission already reviewed.'}, status=400)

        approved = parse_bool(request.data.get('approved', False), default=False)
        message = request.data.get('message', '')

        submission.status = SuspectSubmission.Status.APPROVED if approved else SuspectSubmission.Status.REJECTED
        submission.sergeant = request.user
        submission.sergeant_message = message
        submission.reviewed_at = timezone.now()
        submission.save(update_fields=['status', 'sergeant', 'sergeant_message', 'reviewed_at'])

        if approved:
            submission.suspects.update(status=Suspect.Status.ARRESTED)
            Notification.objects.create(
                recipient=submission.detective,
                case=submission.case,
                message=f'Sergeant approved suspect submission for case #{submission.case.id}. Arrest process started.',
            )
        else:
            Notification.objects.create(
                recipient=submission.detective,
                case=submission.case,
                message=f'Sergeant rejected suspect submission for case #{submission.case.id}: {message}',
            )

        return Response(SuspectSubmissionSerializer(submission).data)


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
