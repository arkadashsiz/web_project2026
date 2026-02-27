from rest_framework import decorators, permissions, status, viewsets
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from cases.models import Case
from investigation.models import Suspect
from rbac.permissions import user_has_action
from .models import Tip, RewardClaim
from .serializers import TipSerializer, RewardClaimSerializer


def has_action(user, action):
    return user.is_superuser or user_has_action(user, action)

User = get_user_model()


POLICE_ROLE_KEYWORDS = [
    'chief', 'captain', 'sergeant', 'detective', 'police officer', 'patrol officer', 'cadet', 'administrator'
]


def is_police_rank_user(user):
    if user.is_superuser:
        return True
    role_names = {r.lower().strip() for r in user.user_roles.values_list('role__name', flat=True)}
    for role_name in role_names:
        if any(k in role_name for k in POLICE_ROLE_KEYWORDS):
            return True
    return False


def is_base_user_only(user):
    if user.is_superuser:
        return False
    role_names = {r.lower().strip() for r in user.user_roles.values_list('role__name', flat=True)}
    return role_names == {'base user'}


class TipViewSet(viewsets.ModelViewSet):
    queryset = Tip.objects.select_related('submitter', 'case', 'suspect').all()
    serializer_class = TipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if has_action(user, 'case.read_all') or has_action(user, 'tip.officer_review') or has_action(user, 'tip.detective_review'):
            if has_action(user, 'tip.detective_review') and not has_action(user, 'case.read_all') and not has_action(user, 'tip.officer_review'):
                return self.queryset.filter(assigned_detective=user).order_by('-created_at')
            return self.queryset.order_by('-created_at')
        return self.queryset.filter(submitter=user).order_by('-created_at')

    def perform_create(self, serializer):
        if not has_action(self.request.user, 'tip.submit'):
            self.permission_denied(self.request, message='No permission')
        if not is_base_user_only(self.request.user):
            self.permission_denied(self.request, message='No permission')
        serializer.save(submitter=self.request.user)

    @decorators.action(detail=False, methods=['get'])
    def case_options(self, request):
        if not has_action(request.user, 'tip.submit'):
            return Response({'detail': 'No permission'}, status=403)
        rows = Case.objects.filter(
            status__in=[Case.Status.OPEN, Case.Status.INVESTIGATING, Case.Status.SENT_TO_COURT]
        ).order_by('-updated_at')[:300]
        return Response([
            {'id': c.id, 'title': c.title, 'status': c.status, 'severity': c.severity}
            for c in rows
        ])

    @decorators.action(detail=False, methods=['get'])
    def suspect_options(self, request):
        if not has_action(request.user, 'tip.submit'):
            return Response({'detail': 'No permission'}, status=403)
        case_id = request.query_params.get('case_id')
        qs = Suspect.objects.select_related('case').all().order_by('-id')
        if case_id:
            qs = qs.filter(case_id=case_id)
        qs = qs[:300]
        return Response([
            {'id': s.id, 'full_name': s.full_name, 'status': s.status, 'case': s.case_id}
            for s in qs
        ])

    @decorators.action(detail=True, methods=['post'])
    def officer_review(self, request, pk=None):
        if not has_action(request.user, 'tip.officer_review'):
            return Response({'detail': 'No permission'}, status=403)

        tip = self.get_object()
        valid = bool(request.data.get('valid', False))
        note = request.data.get('note', '')
        tip.officer_note = note
        if valid:
            responsible_detective = None
            if tip.case and tip.case.assigned_detective_id:
                responsible_detective = tip.case.assigned_detective
            elif tip.suspect and tip.suspect.case and tip.suspect.case.assigned_detective_id:
                responsible_detective = tip.suspect.case.assigned_detective
            if not responsible_detective:
                return Response({'detail': 'No responsible detective found. Assign a detective to the case first.'}, status=400)
            tip.status = Tip.Status.SENT_TO_DETECTIVE
            tip.assigned_detective = responsible_detective
            tip.save(update_fields=['status', 'assigned_detective', 'officer_note'])
        else:
            tip.status = Tip.Status.REJECTED
            tip.save(update_fields=['status', 'officer_note'])
        return Response(self.get_serializer(tip).data)

    @decorators.action(detail=True, methods=['post'])
    def detective_review(self, request, pk=None):
        if not has_action(request.user, 'tip.detective_review'):
            return Response({'detail': 'No permission'}, status=403)

        tip = self.get_object()
        if not request.user.is_superuser and tip.assigned_detective_id and tip.assigned_detective_id != request.user.id:
            return Response({'detail': 'Only assigned detective can review this tip.'}, status=403)
        useful = request.data.get('useful', False)
        note = request.data.get('note', '')
        tip.detective_note = note
        if useful:
            tip.status = Tip.Status.APPROVED
            tip.save(update_fields=['status', 'detective_note'])
            claim, _ = RewardClaim.objects.get_or_create(tip=tip)
            claim.amount = int(request.data.get('amount', 50_000_000))
            claim.save(update_fields=['amount'])
            return Response({'tip': self.get_serializer(tip).data})
        tip.status = Tip.Status.REJECTED
        tip.save(update_fields=['status', 'detective_note'])
        return Response(self.get_serializer(tip).data)


class RewardClaimViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RewardClaim.objects.select_related('tip', 'tip__submitter').all()
    serializer_class = RewardClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tip__submitter=self.request.user)

    @decorators.action(detail=False, methods=['post'])
    def verify(self, request):
        if not (has_action(request.user, 'reward.verify') or is_police_rank_user(request.user)):
            return Response({'detail': 'No permission'}, status=403)

        national_id = request.data.get('national_id')
        unique_code = request.data.get('unique_code')
        claim = RewardClaim.objects.filter(unique_code=unique_code, tip__submitter__national_id=national_id).first()
        if not claim:
            return Response({'detail': 'Invalid claim'}, status=status.HTTP_404_NOT_FOUND)

        claim.verified_by = request.user
        claim.is_paid = True
        claim.save(update_fields=['verified_by', 'is_paid'])
        data = RewardClaimSerializer(claim).data
        data['submitter'] = {
            'id': claim.tip.submitter.id,
            'username': claim.tip.submitter.username,
            'national_id': claim.tip.submitter.national_id,
            'phone': claim.tip.submitter.phone,
            'email': claim.tip.submitter.email,
        }
        return Response(data)
