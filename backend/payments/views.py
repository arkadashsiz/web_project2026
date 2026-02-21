from django.shortcuts import render
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from cases.models import Case
from investigation.models import Suspect
from rbac.permissions import user_has_action
from .models import BailPayment
from .serializers import BailPaymentSerializer


class BailPaymentViewSet(viewsets.ModelViewSet):
    queryset = BailPayment.objects.select_related('case', 'suspect', 'created_by').all()
    serializer_class = BailPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not (request.user.is_superuser or user_has_action(request.user, 'suspect.manage')):
            self.permission_denied(request, message='No permission')

    def perform_create(self, serializer):
        case = serializer.validated_data['case']
        suspect = serializer.validated_data['suspect']

        if case.severity not in [Case.Severity.LEVEL_2, Case.Severity.LEVEL_3]:
            raise ValidationError('Only level 2 and level 3 are eligible for bail/fine release.')
        if suspect.status not in [Suspect.Status.ARRESTED, Suspect.Status.CRIMINAL]:
            raise ValidationError('Payment is only for arrested suspects or level 3 criminals.')

        serializer.save(created_by=self.request.user)

    @decorators.action(detail=True, methods=['post'])
    def callback(self, request, pk=None):
        obj = self.get_object()
        obj.status = request.data.get('status', BailPayment.Status.SUCCESS)
        obj.payment_ref = request.data.get('payment_ref', obj.payment_ref)
        obj.save(update_fields=['status', 'payment_ref'])

        if obj.status == BailPayment.Status.SUCCESS:
            if obj.suspect.status in [Suspect.Status.ARRESTED, Suspect.Status.CRIMINAL]:
                obj.suspect.status = Suspect.Status.CLEARED
                obj.suspect.save(update_fields=['status'])

        return Response(self.get_serializer(obj).data)


def payment_return_page(request):
    payment_ref = request.GET.get('payment_ref', '')
    result = request.GET.get('result', 'unknown')
    return render(request, 'payments/return.html', {'payment_ref': payment_ref, 'result': result})
