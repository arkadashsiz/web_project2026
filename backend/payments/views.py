from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
import json
import ssl
import time
from urllib import request as urllib_request
from urllib import error as urllib_error
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from cases.models import Case
from investigation.models import Suspect
from rbac.permissions import user_has_action
from .models import BailPayment
from .serializers import BailPaymentSerializer


def is_sergeant_user(user):
    if user.is_superuser:
        return True
    role_names = [r.lower().strip() for r in user.user_roles.values_list('role__name', flat=True)]
    return any(x in role_names for x in ['sergeant', 'sergent', 'sargent'])


def zarinpal_post(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib_request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    ssl_verify = getattr(settings, 'ZARINPAL_SSL_VERIFY', True)
    context = None
    if not ssl_verify:
        context = ssl._create_unverified_context()
    try:
        with urllib_request.urlopen(req, timeout=20, context=context) as res:
            body = res.read().decode('utf-8')
        return json.loads(body)
    except urllib_error.HTTPError as exc:
        err_text = ''
        try:
            err_text = exc.read().decode('utf-8')
        except Exception:
            err_text = str(exc)
        # Bubble up gateway response body so frontend can show the real reason.
        raise ValidationError(f'Gateway HTTP {exc.code}: {err_text}')


class BailPaymentViewSet(viewsets.ModelViewSet):
    queryset = BailPayment.objects.select_related('case', 'suspect', 'created_by').all()
    serializer_class = BailPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _can_manage(self, user):
        return user.is_superuser or user_has_action(user, 'suspect.manage')

    def _is_related_suspect(self, user, obj):
        return bool(obj.suspect.person_id and obj.suspect.person_id == user.id)

    def get_queryset(self):
        qs = super().get_queryset()
        if self._can_manage(self.request.user):
            return qs
        return qs.filter(suspect__person=self.request.user)

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'callback'] and not self._can_manage(request.user):
            self.permission_denied(request, message='No permission')

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.action == 'start_gateway':
            # Payment start must be done by the suspect account (or superuser),
            # not by the sergeant/manager who created the payment record.
            if request.user.is_superuser or self._is_related_suspect(request.user, obj):
                return
            self.permission_denied(request, message='Only suspect can start gateway payment')

        if self._can_manage(request.user):
            return
        if self.action in ['list', 'retrieve', 'start_gateway'] and self._is_related_suspect(request.user, obj):
            return
        self.permission_denied(request, message='No permission')

    def perform_create(self, serializer):
        case = serializer.validated_data['case']
        suspect = serializer.validated_data['suspect']
        sergeant_approved = bool(serializer.validated_data.get('sergeant_approved', False))

        if not is_sergeant_user(self.request.user):
            raise ValidationError('Only sergeant can set bail/fine amount.')
        if suspect.case_id != case.id:
            raise ValidationError('Suspect must belong to selected case.')

        # Arrested suspects of level 2/3 can be released via payment.
        if suspect.status == Suspect.Status.ARRESTED:
            if case.severity not in [Case.Severity.LEVEL_2, Case.Severity.LEVEL_3]:
                raise ValidationError('Only level 2 and level 3 arrested suspects are eligible for bail/fine release.')
        # Level 3 criminals can be released only if sergeant approved.
        elif suspect.status == Suspect.Status.CRIMINAL:
            if case.severity != Case.Severity.LEVEL_3:
                raise ValidationError('Only level 3 criminals are eligible for release by fine.')
            if not sergeant_approved:
                raise ValidationError('Sergeant approval is required for level 3 criminal release.')
        else:
            raise ValidationError('Payment is only for arrested suspects or level 3 criminals.')

        serializer.save(created_by=self.request.user)

    @decorators.action(detail=False, methods=['get'])
    def create_options(self, request):
        if not self._can_manage(request.user):
            return Response({'detail': 'No permission'}, status=403)

        eligible_suspects = Suspect.objects.select_related('case').filter(
            Q(status=Suspect.Status.ARRESTED, case__severity__in=[Case.Severity.LEVEL_3, Case.Severity.LEVEL_2])
            | Q(status=Suspect.Status.CRIMINAL, case__severity=Case.Severity.LEVEL_3)
        )

        case_map = {}
        suspects_out = []
        for s in eligible_suspects.order_by('-id'):
            c = s.case
            case_map[c.id] = {
                'id': c.id,
                'title': c.title,
                'severity': c.severity,
                'status': c.status,
            }
            suspects_out.append({
                'id': s.id,
                'full_name': s.full_name,
                'status': s.status,
                'case': c.id,
            })

        return Response({
            'cases': list(case_map.values()),
            'suspects': suspects_out,
        })

    @decorators.action(detail=True, methods=['post'])
    def start_gateway(self, request, pk=None):
        obj = self.get_object()
        self.check_object_permissions(request, obj)

        if obj.status != BailPayment.Status.INITIATED:
            return Response({'detail': 'Payment is not in initiated state.'}, status=400)

        merchant_id = getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
        backend_base = getattr(settings, 'BACKEND_PUBLIC_URL', 'http://localhost:8000').rstrip('/')
        callback_url = f'{backend_base}{reverse("payment-return-page")}?payment_id={obj.id}'
        if int(obj.amount) < 1000:
            return Response({'detail': 'Amount must be at least 1000 for Zarinpal.'}, status=400)

        # Keep payload aligned with Zarinpal sample flow to avoid 422 payload validation issues.
        payload = {
            'merchant_id': merchant_id,
            'amount': int(obj.amount),
            'description': f'Bail/Fine payment for case #{obj.case_id} suspect #{obj.suspect_id}',
            'callback_url': callback_url,
        }

        try:
            result = zarinpal_post(getattr(settings, 'ZARINPAL_REQUEST_URL', ''), payload)
        except Exception as exc:
            return Response({'detail': f'Gateway request failed: {exc}'}, status=502)

        data = result.get('data') or {}
        if data.get('code') == 100:
            authority = data.get('authority', '')
            obj.authority = authority
            obj.gateway_status = str(data.get('code'))
            obj.save(update_fields=['authority', 'gateway_status'])
            start_pay_url = getattr(settings, 'ZARINPAL_STARTPAY_URL', '').format(authority=authority)
            return Response({
                'payment_id': obj.id,
                'authority': authority,
                'start_pay_url': start_pay_url,
                'callback_url': callback_url,
            })

        return Response({'detail': 'Gateway rejected payment request', 'gateway': result}, status=400)

    @decorators.action(detail=True, methods=['post'])
    def callback(self, request, pk=None):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        obj.status = request.data.get('status', BailPayment.Status.SUCCESS)
        obj.payment_ref = request.data.get('payment_ref', obj.payment_ref)
        obj.save(update_fields=['status', 'payment_ref'])

        if obj.status == BailPayment.Status.SUCCESS:
            if obj.suspect.status in [Suspect.Status.ARRESTED, Suspect.Status.CRIMINAL]:
                obj.suspect.status = Suspect.Status.CLEARED
                obj.suspect.save(update_fields=['status'])

        return Response(self.get_serializer(obj).data)


def payment_return_page(request):
    payment_id = request.GET.get('payment_id')
    authority = request.GET.get('Authority', '')
    gateway_status = request.GET.get('Status', '')

    context = {
        'payment_ref': '',
        'result': 'failed',
        'payment_id': payment_id or '',
        'authority': authority,
        'message': 'Unknown payment callback state.',
    }
    frontend_base = getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:5173').rstrip('/')
    context['frontend_return_url'] = f'{frontend_base}/payments?payment_id={payment_id or ""}&result=failed&t={int(time.time())}'

    if not payment_id:
        context['message'] = 'Missing payment_id in callback.'
        return render(request, 'payments/return.html', context)

    obj = BailPayment.objects.filter(id=payment_id).select_related('suspect', 'case').first()
    if not obj:
        context['message'] = 'Payment record not found.'
        return render(request, 'payments/return.html', context)

    context['payment_id'] = obj.id
    context['amount'] = obj.amount

    if gateway_status != 'OK':
        obj.status = BailPayment.Status.FAILED
        obj.gateway_status = gateway_status or 'NOK'
        obj.save(update_fields=['status', 'gateway_status'])
        context['result'] = 'failed'
        context['message'] = 'Payment was canceled or failed on gateway.'
        context['frontend_return_url'] = f'{frontend_base}/payments?payment_id={obj.id}&result=failed&t={int(time.time())}'
        return render(request, 'payments/return.html', context)

    merchant_id = getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
    verify_payload = {
        'merchant_id': merchant_id,
        'amount': int(obj.amount),
        'authority': authority,
    }
    try:
        result = zarinpal_post(getattr(settings, 'ZARINPAL_VERIFY_URL', ''), verify_payload)
    except Exception as exc:
        obj.status = BailPayment.Status.FAILED
        obj.gateway_status = 'verify_error'
        obj.save(update_fields=['status', 'gateway_status'])
        context['message'] = f'Gateway verify failed: {exc}'
        context['frontend_return_url'] = f'{frontend_base}/payments?payment_id={obj.id}&result=failed&t={int(time.time())}'
        return render(request, 'payments/return.html', context)

    data = result.get('data') or {}
    if data.get('code') in [100, 101]:
        obj.status = BailPayment.Status.SUCCESS
        obj.payment_ref = str(data.get('ref_id') or '')
        obj.authority = authority or obj.authority
        obj.gateway_status = str(data.get('code'))
        obj.save(update_fields=['status', 'payment_ref', 'authority', 'gateway_status'])
        if obj.suspect.status in [Suspect.Status.ARRESTED, Suspect.Status.CRIMINAL]:
            obj.suspect.status = Suspect.Status.CLEARED
            obj.suspect.save(update_fields=['status'])
        context['payment_ref'] = obj.payment_ref
        context['result'] = 'success'
        context['message'] = 'Payment verified successfully.'
        context['frontend_return_url'] = f'{frontend_base}/payments?payment_id={obj.id}&result=success&t={int(time.time())}'
    else:
        obj.status = BailPayment.Status.FAILED
        obj.gateway_status = str(data.get('code') or 'verify_failed')
        obj.save(update_fields=['status', 'gateway_status'])
        context['message'] = f"Verification failed with code {data.get('code')}."
        context['frontend_return_url'] = f'{frontend_base}/payments?payment_id={obj.id}&result=failed&t={int(time.time())}'

    return render(request, 'payments/return.html', context)
