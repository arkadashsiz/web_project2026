from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from rbac.models import Role, RolePermission, UserRole

User = get_user_model()


class RewardFlowTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reporter', password='Strong12345', email='r@example.com', phone='09126666666', national_id='666'
        )
        submit_role = Role.objects.create(name='complainant')
        RolePermission.objects.create(role=submit_role, action='tip.submit')
        UserRole.objects.create(user=self.user, role=submit_role)
        self.client.force_authenticate(self.user)

    def test_tip_submit(self):
        resp = self.client.post('/api/rewards/tips/', {'content': 'I saw the suspect near market'}, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_tip_review_chain(self):
        tip = self.client.post('/api/rewards/tips/', {'content': 'new info'}, format='json').data

        officer = User.objects.create_user(
            username='off1', password='Strong12345', email='o@example.com', phone='09127777777', national_id='777'
        )
        officer_role = Role.objects.create(name='police officer')
        RolePermission.objects.create(role=officer_role, action='tip.officer_review')
        UserRole.objects.create(user=officer, role=officer_role)

        detective = User.objects.create_user(
            username='det1', password='Strong12345', email='det@example.com', phone='09128888888', national_id='888'
        )
        detective_role = Role.objects.create(name='detective')
        RolePermission.objects.create(role=detective_role, action='tip.detective_review')
        UserRole.objects.create(user=detective, role=detective_role)

        self.client.force_authenticate(officer)
        resp1 = self.client.post(f"/api/rewards/tips/{tip['id']}/officer_review/", {'valid': True}, format='json')
        self.assertEqual(resp1.status_code, 200)

        self.client.force_authenticate(detective)
        resp2 = self.client.post(f"/api/rewards/tips/{tip['id']}/detective_review/", {'useful': True, 'amount': 1234}, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data['claim']['amount'], 1234)
