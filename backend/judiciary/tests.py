from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from cases.models import Case
from investigation.models import Suspect
from judiciary.models import CourtSession
from rbac.models import Role, RolePermission, UserRole

User = get_user_model()


class JudiciaryFlowTest(APITestCase):
    def setUp(self):
        self.judge = User.objects.create_user(
            username='judge1', password='Strong12345', email='j@example.com', phone='09125555555', national_id='555'
        )
        role = Role.objects.create(name='judge')
        RolePermission.objects.create(role=role, action='judiciary.verdict')
        UserRole.objects.create(user=self.judge, role=role)
        self.client.force_authenticate(self.judge)

        self.case = Case.objects.create(
            title='Case B', description='desc', source=Case.Source.SCENE, status=Case.Status.SENT_TO_COURT,
            severity=Case.Severity.LEVEL_2, created_by=self.judge,
        )
        self.suspect = Suspect.objects.create(case=self.case, full_name='Sus A', national_id='2233')
        self.suspect2 = Suspect.objects.create(case=self.case, full_name='Sus B', national_id='2234')

    def test_verdict_closes_case_and_updates_suspect(self):
        resp = self.client.post('/api/judiciary/court-sessions/', {
            'case': self.case.id,
            'verdict': CourtSession.Verdict.GUILTY,
            'convicted_suspect': self.suspect.id,
            'punishment_title': 'Jail',
            'punishment_description': '2 years',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

        self.case.refresh_from_db()
        self.suspect.refresh_from_db()
        self.suspect2.refresh_from_db()
        self.assertEqual(self.case.status, Case.Status.SENT_TO_COURT)
        self.assertEqual(self.suspect.status, Suspect.Status.CRIMINAL)

        resp2 = self.client.post('/api/judiciary/court-sessions/', {
            'case': self.case.id,
            'verdict': CourtSession.Verdict.NOT_GUILTY,
            'convicted_suspect': self.suspect2.id,
            'punishment_title': '',
            'punishment_description': '',
        }, format='json')
        self.assertEqual(resp2.status_code, 201)

        self.case.refresh_from_db()
        self.suspect2.refresh_from_db()
        self.assertEqual(self.case.status, Case.Status.CLOSED)
        self.assertEqual(self.suspect2.status, Suspect.Status.CLEARED)

    def test_case_summary_endpoint(self):
        resp = self.client.get(f'/api/judiciary/court-sessions/case_summary/?case_id={self.case.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['case']['id'], self.case.id)
        self.assertIn('involved_members', resp.data)
        self.assertIn('evidence', resp.data)
        self.assertIn('complainant_details', resp.data)
        self.assertIn('court_sessions', resp.data)
