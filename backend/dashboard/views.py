from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cases.models import Case
from investigation.models import Suspect
from rbac.permissions import user_has_action

User = get_user_model()


def _modules_for_user(user):
    role_names = set(user.user_roles.values_list('role__name', flat=True))
    modules = [{'key': 'cases', 'title': 'Case Management', 'path': '/cases'}]

    if user.is_superuser or user_has_action(user, 'evidence.manage') or user_has_action(user, 'evidence.biological.review'):
        modules.append({'key': 'evidence', 'title': 'Evidence Registry', 'path': '/evidence'})

    if user.is_superuser or user_has_action(user, 'investigation.board.manage'):
        modules.append({'key': 'detective_board', 'title': 'Detective Board', 'path': '/board'})
    if user.is_superuser or user_has_action(user, 'suspect.manage'):
        modules.append({'key': 'sergeant_review', 'title': 'Suspect Reviews', 'path': '/board'})
    if user.is_superuser or user_has_action(user, 'interrogation.captain_decision') or user_has_action(user, 'interrogation.chief_review'):
        modules.append({'key': 'interrogation_reviews', 'title': 'Interrogation Reviews', 'path': '/board'})

    if user.is_superuser or role_names.intersection({'captain', 'chief', 'judge'}) or user_has_action(user, 'case.send_to_court'):
        modules.append({'key': 'reports', 'title': 'Global Reports', 'path': '/reports'})

    if user.is_superuser or role_names.intersection({'judge'}) or user_has_action(user, 'judiciary.verdict'):
        modules.append({'key': 'judiciary', 'title': 'Judiciary', 'path': '/judiciary'})

    if user.is_superuser or role_names.intersection({'police officer', 'detective'}) or user_has_action(user, 'tip.detective_review') or user_has_action(user, 'tip.submit'):
        modules.append({'key': 'rewards', 'title': 'Rewards & Tips', 'path': '/rewards'})

    has_suspect_profile = Suspect.objects.filter(person=user).exists()
    if (
        user.is_superuser
        or user_has_action(user, 'suspect.manage')
        or role_names.intersection({'suspect', 'criminal'})
        or has_suspect_profile
    ):
        modules.append({'key': 'payments', 'title': 'Payments', 'path': '/payments'})

    if user.is_superuser:
        modules.append({'key': 'rbac_admin', 'title': 'RBAC Admin', 'path': '/admin-rbac'})

    return modules


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    return Response({
        'resolved_cases': Case.objects.filter(status=Case.Status.CLOSED).count(),
        'employees': User.objects.exclude(user_roles__role__name='base user').distinct().count(),
        'active_cases': Case.objects.exclude(status__in=[Case.Status.CLOSED, Case.Status.VOID]).count(),
        'total_cases': Case.objects.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def modules(request):
    return Response({'modules': _modules_for_user(request.user)})
