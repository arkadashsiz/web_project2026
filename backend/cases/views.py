from django.db.models import Q
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.response import Response

from rbac.permissions import user_has_action
from .models import Case, ComplaintSubmission, CaseComplainant, CaseWitness, CaseLog
from .serializers import (
    CaseSerializer,
    ComplaintSubmissionSerializer,
    CaseComplainantSerializer,
    CaseWitnessSerializer,
)


def log_case(case, user, action, details=''):
    CaseLog.objects.create(case=case, actor=user, action=action, details=details)


def has_any_action(user, actions):
    return user.is_superuser or any(user_has_action(user, a) for a in actions)


POLICE_RANK = {
    'cadet': 1,
    'patrol officer': 2,
    'police officer': 3,
    'detective': 3,
    'sergeant': 4,
    'captain': 5,
    'chief': 6,
}


def user_rank(user):
    role_names = [r.lower() for r in user.user_roles.values_list('role__name', flat=True)]
    ranks = [POLICE_RANK[r] for r in role_names if r in POLICE_RANK]
    return max(ranks) if ranks else 0


def is_non_cadet_police(user):
    return user_rank(user) >= POLICE_RANK['patrol officer']


def is_any_superior(approver, creator):
    return user_rank(approver) > user_rank(creator)


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all().select_related('created_by', 'assigned_detective')
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if has_any_action(self.request.user, ['case.read_all']):
            return self.queryset.order_by('-updated_at')
        return self.queryset.filter(
            Q(created_by=self.request.user) | Q(complainants__user=self.request.user)
        ).distinct().order_by('-updated_at')

    def perform_create(self, serializer):
        case = serializer.save(created_by=self.request.user)
        log_case(case, self.request.user, 'case.created')

    @decorators.action(detail=False, methods=['post'])
    def submit_complaint(self, request):
        data = request.data.copy()
        data['source'] = Case.Source.COMPLAINT
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        case = serializer.save(created_by=request.user, status=Case.Status.UNDER_REVIEW)

        ComplaintSubmission.objects.create(case=case, complainant=request.user, stage=ComplaintSubmission.Stage.TO_CADET)
        CaseComplainant.objects.create(case=case, user=request.user, status=CaseComplainant.Status.PENDING)

        for user_id in request.data.get('additional_complainant_ids', []):
            if int(user_id) == request.user.id:
                continue
            CaseComplainant.objects.get_or_create(
                case=case,
                user_id=int(user_id),
                defaults={'status': CaseComplainant.Status.PENDING},
            )
        log_case(case, request.user, 'complaint.submitted')
        return Response(self.get_serializer(case).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['post'])
    def submit_scene_report(self, request):
        allowed = request.user.is_superuser or is_non_cadet_police(request.user) or has_any_action(request.user, ['case.scene.create'])
        if not allowed:
            return Response({'detail': 'No permission'}, status=403)

        data = request.data.copy()
        data['source'] = Case.Source.SCENE
        if not data.get('scene_reported_at'):
            return Response({'detail': 'scene_reported_at is required for scene-based case'}, status=400)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        if request.user.is_superuser or user_rank(request.user) >= POLICE_RANK['chief']:
            next_status = Case.Status.OPEN
        else:
            next_status = Case.Status.UNDER_REVIEW

        case = serializer.save(created_by=request.user, status=next_status)

        witnesses = request.data.get('witnesses', [])
        for witness in witnesses:
            CaseWitness.objects.create(case=case, **witness)
        log_case(case, request.user, 'scene.reported')
        return Response(self.get_serializer(case).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=['post'])
    def approve_scene(self, request, pk=None):
        if not has_any_action(request.user, ['case.complaint.officer_review', 'case.send_to_court', 'case.scene.create']):
            return Response({'detail': 'No permission'}, status=403)
        case = self.get_object()
        if case.source != Case.Source.SCENE:
            return Response({'detail': 'Not scene-based case'}, status=400)
        if case.status != Case.Status.UNDER_REVIEW:
            return Response({'detail': 'Scene case is not awaiting approval'}, status=400)

        creator_rank = user_rank(case.created_by)
        if creator_rank == 0:
            return Response({'detail': 'Invalid reporter role for scene case'}, status=400)
        if creator_rank >= POLICE_RANK['chief']:
            return Response({'detail': 'Chief-created scene case does not require approval'}, status=400)
        if not request.user.is_superuser and not is_any_superior(request.user, case.created_by):
            return Response({'detail': 'Only superior ranks can approve this scene case'}, status=403)

        case.status = Case.Status.OPEN
        case.save(update_fields=['status', 'updated_at'])
        log_case(case, request.user, 'scene.approved')
        return Response(self.get_serializer(case).data)

    @decorators.action(detail=True, methods=['post'])
    def deny_scene(self, request, pk=None):
        if not has_any_action(request.user, ['case.complaint.officer_review', 'case.send_to_court', 'case.scene.create']):
            return Response({'detail': 'No permission'}, status=403)
        case = self.get_object()
        if case.source != Case.Source.SCENE:
            return Response({'detail': 'Not scene-based case'}, status=400)
        if case.status != Case.Status.UNDER_REVIEW:
            return Response({'detail': 'Scene case is not awaiting approval'}, status=400)

        creator_rank = user_rank(case.created_by)
        if creator_rank == 0:
            return Response({'detail': 'Invalid reporter role for scene case'}, status=400)
        if creator_rank >= POLICE_RANK['chief']:
            return Response({'detail': 'Chief-created scene case does not require approval'}, status=400)
        if not request.user.is_superuser and not is_any_superior(request.user, case.created_by):
            return Response({'detail': 'Only superior ranks can deny this scene case'}, status=403)

        note = request.data.get('note', '')
        case.status = Case.Status.VOID
        case.save(update_fields=['status', 'updated_at'])
        log_case(case, request.user, 'scene.denied', note)
        return Response(self.get_serializer(case).data)

    @decorators.action(detail=True, methods=['post'])
    def add_scene_complainant(self, request, pk=None):
        case = self.get_object()
        if case.source != Case.Source.SCENE:
            return Response({'detail': 'Only scene cases can add complainants by this endpoint'}, status=400)
        if not has_any_action(request.user, ['case.scene.add_complainant']):
            return Response({'detail': 'No permission'}, status=403)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=400)

        obj, created = CaseComplainant.objects.get_or_create(
            case=case,
            user_id=int(user_id),
            defaults={'status': CaseComplainant.Status.PENDING},
        )
        if not created:
            return Response({'detail': 'Complainant already exists for this case'}, status=400)
        log_case(case, request.user, 'scene.complainant.added', f'user_id={user_id}')
        return Response(CaseComplainantSerializer(obj).data, status=201)

    @decorators.action(detail=True, methods=['post'])
    def intern_review(self, request, pk=None):
        if not has_any_action(request.user, ['case.complaint.intern_review']):
            return Response({'detail': 'No permission'}, status=403)

        case = self.get_object()
        sub = getattr(case, 'complaint_submission', None)
        if not sub:
            return Response({'detail': 'Not complaint-based case'}, status=400)
        if sub.stage not in [ComplaintSubmission.Stage.TO_CADET, ComplaintSubmission.Stage.RETURNED_TO_CADET]:
            return Response({'detail': 'Case is not awaiting cadet review'}, status=400)

        approved = request.data.get('approved', False)
        note = request.data.get('note', '')
        sub.intern_note = note

        if approved:
            pending = CaseComplainant.objects.filter(case=case, status=CaseComplainant.Status.PENDING).exists()
            if pending:
                return Response({'detail': 'All complainants must be approved/rejected by cadet first'}, status=400)
            case.status = Case.Status.UNDER_REVIEW
            sub.stage = ComplaintSubmission.Stage.TO_OFFICER
            sub.last_error_message = ''
            case.save(update_fields=['status', 'updated_at'])
            log_case(case, request.user, 'complaint.intern.approved', note)
        else:
            if not note.strip():
                return Response({'detail': 'Cadet rejection must include error message'}, status=400)
            sub.attempt_count += 1
            if sub.attempt_count >= 3:
                case.status = Case.Status.VOID
                sub.stage = ComplaintSubmission.Stage.VOIDED
                sub.last_error_message = note
                case.save(update_fields=['status', 'updated_at'])
                log_case(case, request.user, 'complaint.void', note)
            else:
                case.status = Case.Status.DRAFT
                sub.stage = ComplaintSubmission.Stage.RETURNED_TO_COMPLAINANT
                sub.last_error_message = note
                case.save(update_fields=['status', 'updated_at'])
                log_case(case, request.user, 'complaint.returned_to_complainant', note)

        sub.save()
        return Response({
            'case_status': case.status,
            'attempt_count': sub.attempt_count,
            'stage': sub.stage,
            'last_error_message': sub.last_error_message,
        })

    @decorators.action(detail=True, methods=['post'])
    def officer_review(self, request, pk=None):
        if not has_any_action(request.user, ['case.complaint.officer_review']):
            return Response({'detail': 'No permission'}, status=403)

        case = self.get_object()
        sub = getattr(case, 'complaint_submission', None)
        if not sub:
            return Response({'detail': 'Not complaint-based case'}, status=400)
        if sub.stage != ComplaintSubmission.Stage.TO_OFFICER:
            return Response({'detail': 'Case is not awaiting officer review'}, status=400)

        approved = request.data.get('approved', False)
        note = request.data.get('note', '')
        sub.officer_note = note

        if approved:
            approved_any = CaseComplainant.objects.filter(case=case, status=CaseComplainant.Status.APPROVED).exists()
            pending = CaseComplainant.objects.filter(case=case, status=CaseComplainant.Status.PENDING).exists()
            if pending or not approved_any:
                return Response({'detail': 'Complainant verification by cadet is incomplete'}, status=400)
            case.status = Case.Status.OPEN
            sub.stage = ComplaintSubmission.Stage.FORMED
            sub.last_error_message = ''
            log_case(case, request.user, 'complaint.officer.approved', note)
        else:
            case.status = Case.Status.UNDER_REVIEW
            sub.stage = ComplaintSubmission.Stage.RETURNED_TO_CADET
            sub.last_error_message = note
            log_case(case, request.user, 'complaint.officer.returned_to_intern', note)

        case.save(update_fields=['status', 'updated_at'])
        sub.save(update_fields=['officer_note', 'stage', 'last_error_message'])
        return Response({'case_status': case.status, 'stage': sub.stage, 'last_error_message': sub.last_error_message})

    @decorators.action(detail=True, methods=['post'])
    def resubmit_complaint(self, request, pk=None):
        case = self.get_object()
        sub = getattr(case, 'complaint_submission', None)
        if not sub:
            return Response({'detail': 'Not complaint-based case'}, status=400)

        is_owner = case.created_by_id == request.user.id or case.complainants.filter(user=request.user).exists()
        if not is_owner and not request.user.is_superuser:
            return Response({'detail': 'Only complainant can resubmit'}, status=403)
        if sub.stage != ComplaintSubmission.Stage.RETURNED_TO_COMPLAINANT:
            return Response({'detail': 'Case is not awaiting complainant resubmission'}, status=400)
        if sub.attempt_count >= 3 or case.status == Case.Status.VOID:
            return Response({'detail': 'Case is voided and cannot be resubmitted'}, status=400)

        for field in ['title', 'description', 'severity']:
            if field in request.data:
                setattr(case, field, request.data.get(field))
        case.status = Case.Status.UNDER_REVIEW
        case.save(update_fields=['title', 'description', 'severity', 'status', 'updated_at'])

        for user_id in request.data.get('additional_complainant_ids', []):
            if int(user_id) == case.created_by_id:
                continue
            CaseComplainant.objects.get_or_create(
                case=case,
                user_id=int(user_id),
                defaults={'status': CaseComplainant.Status.PENDING},
            )

        sub.stage = ComplaintSubmission.Stage.TO_CADET
        sub.last_error_message = ''
        sub.save(update_fields=['stage', 'last_error_message'])
        log_case(case, request.user, 'complaint.resubmitted')
        return Response(self.get_serializer(case).data)

    @decorators.action(detail=True, methods=['post'])
    def intern_review_complainant(self, request, pk=None):
        if not has_any_action(request.user, ['case.complaint.intern_review']):
            return Response({'detail': 'No permission'}, status=403)

        case = self.get_object()
        sub = getattr(case, 'complaint_submission', None)
        if not sub:
            return Response({'detail': 'Not complaint-based case'}, status=400)
        if sub.stage not in [ComplaintSubmission.Stage.TO_CADET, ComplaintSubmission.Stage.RETURNED_TO_CADET]:
            return Response({'detail': 'Case is not awaiting cadet review'}, status=400)

        complainant_id = request.data.get('complainant_id')
        approved = bool(request.data.get('approved', False))
        note = request.data.get('note', '')
        if complainant_id is None:
            return Response({'detail': 'complainant_id is required'}, status=400)

        complainant = case.complainants.filter(id=complainant_id).first()
        if not complainant:
            return Response({'detail': 'Complainant record not found for this case'}, status=404)

        complainant.status = CaseComplainant.Status.APPROVED if approved else CaseComplainant.Status.REJECTED
        complainant.review_note = note
        complainant.save(update_fields=['status', 'review_note'])
        log_case(case, request.user, 'complainant.reviewed', f'complainant={complainant.user_id}, status={complainant.status}')
        return Response(CaseComplainantSerializer(complainant).data)

    @decorators.action(detail=True, methods=['post'])
    def assign_detective(self, request, pk=None):
        if not has_any_action(request.user, ['case.assign_detective']):
            return Response({'detail': 'No permission'}, status=403)

        case = self.get_object()
        detective_id = request.data.get('detective_id')
        if detective_id is None:
            return Response({'detail': 'detective_id required'}, status=400)

        case.assigned_detective_id = detective_id
        case.status = Case.Status.INVESTIGATING
        case.save(update_fields=['assigned_detective', 'status', 'updated_at'])
        log_case(case, request.user, 'case.detective.assigned', f'detective={detective_id}')
        return Response(self.get_serializer(case).data)

    @decorators.action(detail=True, methods=['post'])
    def send_to_court(self, request, pk=None):
        if not has_any_action(request.user, ['case.send_to_court']):
            return Response({'detail': 'No permission'}, status=403)
        case = self.get_object()
        case.status = Case.Status.SENT_TO_COURT
        case.save(update_fields=['status', 'updated_at'])
        log_case(case, request.user, 'case.sent_to_court')
        return Response(self.get_serializer(case).data)


class ComplaintSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComplaintSubmission.objects.select_related('case', 'complainant').all()
    serializer_class = ComplaintSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if has_any_action(user, ['case.read_all']):
            return self.queryset.order_by('-id')
        return self.queryset.filter(
            Q(case__created_by=user) | Q(case__complainants__user=user)
        ).distinct().order_by('-id')


class CaseComplainantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CaseComplainant.objects.select_related('case', 'user').all()
    serializer_class = CaseComplainantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if has_any_action(user, ['case.read_all']):
            return self.queryset.order_by('-id')
        return self.queryset.filter(
            Q(case__created_by=user) | Q(case__complainants__user=user)
        ).distinct().order_by('-id')


class CaseWitnessViewSet(viewsets.ModelViewSet):
    queryset = CaseWitness.objects.select_related('case').all()
    serializer_class = CaseWitnessSerializer
    permission_classes = [permissions.IsAuthenticated]
