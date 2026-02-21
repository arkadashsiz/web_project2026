from rest_framework import permissions, viewsets

from cases.models import Case
from investigation.models import Suspect
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

    def perform_create(self, serializer):
        session = serializer.save(judge=self.request.user)
        case = session.case
        case.status = Case.Status.CLOSED
        case.save(update_fields=['status', 'updated_at'])

        suspects = Suspect.objects.filter(case=case)
        if session.verdict == CourtSession.Verdict.GUILTY:
            suspects.update(status=Suspect.Status.CRIMINAL)
        else:
            suspects.update(status=Suspect.Status.CLEARED)
