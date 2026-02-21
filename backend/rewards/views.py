from rest_framework import decorators, permissions, status, viewsets
from rest_framework.response import Response

from rbac.permissions import user_has_action
from .models import Tip, RewardClaim
from .serializers import TipSerializer, RewardClaimSerializer


def has_action(user, action):
    return user.is_superuser or user_has_action(user, action)


class TipViewSet(viewsets.ModelViewSet):
    queryset = Tip.objects.select_related('submitter', 'case', 'suspect').all()
    serializer_class = TipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if has_action(user, 'case.read_all') or has_action(user, 'tip.officer_review') or has_action(user, 'tip.detective_review'):
            return self.queryset.order_by('-created_at')
        return self.queryset.filter(submitter=user).order_by('-created_at')

    def perform_create(self, serializer):
        if not has_action(self.request.user, 'tip.submit'):
            self.permission_denied(self.request, message='No permission')
        serializer.save(submitter=self.request.user)

    @decorators.action(detail=True, methods=['post'])
    def officer_review(self, request, pk=None):
        if not has_action(request.user, 'tip.officer_review'):
            return Response({'detail': 'No permission'}, status=403)

        tip = self.get_object()
        valid = request.data.get('valid', False)
        tip.status = Tip.Status.SENT_TO_DETECTIVE if valid else Tip.Status.REJECTED
        tip.save(update_fields=['status'])
        return Response(self.get_serializer(tip).data)

    @decorators.action(detail=True, methods=['post'])
    def detective_review(self, request, pk=None):
        if not has_action(request.user, 'tip.detective_review'):
            return Response({'detail': 'No permission'}, status=403)

        tip = self.get_object()
        useful = request.data.get('useful', False)
        if useful:
            tip.status = Tip.Status.APPROVED
            tip.save(update_fields=['status'])
            claim, _ = RewardClaim.objects.get_or_create(tip=tip)
            claim.amount = int(request.data.get('amount', 50_000_000))
            claim.save(update_fields=['amount'])
            return Response({'tip': self.get_serializer(tip).data, 'claim': RewardClaimSerializer(claim).data})
        tip.status = Tip.Status.REJECTED
        tip.save(update_fields=['status'])
        return Response(self.get_serializer(tip).data)


class RewardClaimViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RewardClaim.objects.select_related('tip', 'tip__submitter').all()
    serializer_class = RewardClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=['post'])
    def verify(self, request):
        if not has_action(request.user, 'reward.verify'):
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
