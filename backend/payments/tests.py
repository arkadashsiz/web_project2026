from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from cases.models import Case
from investigation.models import Suspect
from rbac.models import Role, RolePermission, UserRole

User = get_user_model()


class PaymentFlowTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='serg1', password='Strong12345', email='s@example.com', phone='09129999999', national_id='999'
        )
        role = Role.objects.create(name='sergeant')
        RolePermission.objects.create(role=role, action='suspect.manage')
        UserRole.objects.create(user=self.user, role=role)
        self.client.force_authenticate(self.user)

        self.case = Case.objects.create(
            title='Case P', description='desc', source=Case.Source.SCENE, status=Case.Status.OPEN,
            severity=Case.Severity.LEVEL_2, created_by=self.user,
        )
        self.suspect = Suspect.objects.create(case=self.case, full_name='Sus P', national_id='1199', status=Suspect.Status.ARRESTED)

    def test_bail_create_and_callback(self):
        resp = self.client.post('/api/payments/bail/', {
            'case': self.case.id,
            'suspect': self.suspect.id,
            'amount': 400000,
        }, format='json')
        self.assertEqual(resp.status_code, 201)

        pid = resp.data['id']
        cb = self.client.post(f'/api/payments/bail/{pid}/callback/', {'status': 'success', 'payment_ref': 'ABC1'}, format='json')
        self.assertEqual(cb.status_code, 200)

    def test_bail_create_requires_amount(self):
        resp = self.client.post('/api/payments/bail/', {
            'case': self.case.id,
            'suspect': self.suspect.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('amount', resp.data)
