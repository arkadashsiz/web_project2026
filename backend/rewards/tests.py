from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from cases.models import Case
from investigation.models import Suspect
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
        self.case = Case.objects.create(
            title='Reward flow case',
            description='desc',
            source=Case.Source.SCENE,
            status=Case.Status.INVESTIGATING,
            severity=Case.Severity.LEVEL_2,
            created_by=self.user,
        )
        self.suspect = Suspect.objects.create(case=self.case, full_name='Reward Suspect')

    def test_tip_submit(self):
        resp = self.client.post('/api/rewards/tips/', {
            'content': 'I saw the suspect near market',
            'case': self.case.id,
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_tip_review_chain(self):
        tip = self.client.post('/api/rewards/tips/', {
            'content': 'new info',
            'suspect': self.suspect.id,
        }, format='json').data

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
        self.case.assigned_detective = detective
        self.case.save(update_fields=['assigned_detective'])

        self.client.force_authenticate(officer)
        resp1 = self.client.post(f"/api/rewards/tips/{tip['id']}/officer_review/", {'valid': True, 'note': 'forwarding'}, format='json')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.data['status'], 'sent_to_detective')
        self.assertEqual(resp1.data['assigned_detective'], detective.id)

        self.client.force_authenticate(detective)
        resp2 = self.client.post(f"/api/rewards/tips/{tip['id']}/detective_review/", {'useful': True, 'amount': 1234, 'note': 'valid'}, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data['claim']['amount'], 1234)
        self.assertTrue(resp2.data['claim']['unique_code'])

    def test_police_rank_can_verify_by_national_id_and_code(self):
        tip = self.client.post('/api/rewards/tips/', {
            'content': 'tip verify',
            'case': self.case.id,
        }, format='json').data

        officer = User.objects.create_user(
            username='off2', password='Strong12345', email='o2@example.com', phone='09129990000', national_id='999'
        )
        officer_role = Role.objects.create(name='police officer 2')
        RolePermission.objects.create(role=officer_role, action='tip.officer_review')
        UserRole.objects.create(user=officer, role=officer_role)

        detective = User.objects.create_user(
            username='det2', password='Strong12345', email='det2@example.com', phone='09129990001', national_id='998'
        )
        detective_role = Role.objects.create(name='detective 2')
        RolePermission.objects.create(role=detective_role, action='tip.detective_review')
        UserRole.objects.create(user=detective, role=detective_role)
        self.case.assigned_detective = detective
        self.case.save(update_fields=['assigned_detective'])

        self.client.force_authenticate(officer)
        self.client.post(f"/api/rewards/tips/{tip['id']}/officer_review/", {'valid': True}, format='json')
        self.client.force_authenticate(detective)
        approved = self.client.post(f"/api/rewards/tips/{tip['id']}/detective_review/", {'useful': True, 'amount': 9999}, format='json').data
        code = approved['claim']['unique_code']

        sergeant = User.objects.create_user(
            username='ser_verify', password='Strong12345', email='sv@example.com', phone='09129990002', national_id='997'
        )
        sergeant_role = Role.objects.create(name='sergeant verify')
        UserRole.objects.create(user=sergeant, role=sergeant_role)
        self.client.force_authenticate(sergeant)
        v = self.client.post('/api/rewards/reward-claims/verify/', {
            'national_id': self.user.national_id,
            'unique_code': code,
        }, format='json')
        self.assertEqual(v.status_code, 200)
        self.assertEqual(v.data['amount'], 9999)
