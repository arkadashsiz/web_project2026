from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from cases.models import Case
from rbac.models import Role, RolePermission, UserRole

User = get_user_model()


class InvestigationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='detective',
            password='Strong12345',
            email='d@example.com',
            phone='09124444444',
            national_id='444',
        )
        role = Role.objects.create(name='detective')
        RolePermission.objects.create(role=role, action='suspect.manage')
        UserRole.objects.create(user=self.user, role=role)
        self.client.force_authenticate(self.user)

        self.case = Case.objects.create(
            title='Case A',
            description='desc',
            source=Case.Source.SCENE,
            status=Case.Status.OPEN,
            severity=Case.Severity.LEVEL_1,
            created_by=self.user,
        )

    def test_create_suspect(self):
        resp = self.client.post('/api/investigation/suspects/', {
            'case': self.case.id,
            'full_name': 'John Doe',
            'national_id': '9999',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_high_alert_formula(self):
        resp = self.client.post('/api/investigation/suspects/', {
            'case': self.case.id,
            'full_name': 'Old Suspect',
            'national_id': '9988',
        }, format='json')
        sid = resp.data['id']

        from investigation.models import Suspect
        s = Suspect.objects.get(id=sid)
        s.marked_at = timezone.now() - timedelta(days=40)
        s.save(update_fields=['marked_at'])

        result = self.client.get('/api/investigation/high-alert/')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(any(x['national_id'] == '9988' for x in result.data))
