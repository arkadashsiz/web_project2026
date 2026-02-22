from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from cases.models import Case
from evidence.models import WitnessEvidence
from rbac.models import Role, RolePermission, UserRole

User = get_user_model()


class BoardOpenCaseTests(APITestCase):
    def setUp(self):
        self.detective = User.objects.create_user(
            username='det_board',
            password='Strong12345',
            email='detb@example.com',
            phone='09134444444',
            national_id='3444',
        )
        d_role = Role.objects.create(name='detective_board_role')
        RolePermission.objects.create(role=d_role, action='investigation.board.manage')
        UserRole.objects.create(user=self.detective, role=d_role)

        self.case = Case.objects.create(
            title='Case Board',
            description='desc',
            source=Case.Source.COMPLAINT,
            status=Case.Status.INVESTIGATING,
            severity=Case.Severity.LEVEL_2,
            created_by=self.detective,
            assigned_detective=self.detective,
        )

    def test_assigned_detective_can_open_case_board(self):
        self.client.force_authenticate(self.detective)
        resp = self.client.post('/api/investigation/boards/open_case_board/', {'case_id': self.case.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['case']['id'], self.case.id)
        self.assertIn('board', resp.data)
        self.assertIn('evidence', resp.data)

    def test_non_assigned_detective_cannot_open(self):
        other = User.objects.create_user(
            username='det_other',
            password='Strong12345',
            email='deto@example.com',
            phone='09135555555',
            national_id='3555',
        )
        d_role2 = Role.objects.create(name='detective_board_role_2')
        RolePermission.objects.create(role=d_role2, action='investigation.board.manage')
        UserRole.objects.create(user=other, role=d_role2)

        self.client.force_authenticate(other)
        resp = self.client.post('/api/investigation/boards/open_case_board/', {'case_id': self.case.id}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_open_board_syncs_new_evidence_cards(self):
        self.client.force_authenticate(self.detective)
        first = self.client.post('/api/investigation/boards/open_case_board/', {'case_id': self.case.id}, format='json')
        self.assertEqual(first.status_code, 200)
        initial_count = len(first.data['board']['nodes'])

        WitnessEvidence.objects.create(
            case=self.case,
            title='Witness clip',
            description='clip from local witness',
            recorded_by=self.detective,
            transcript='saw suspect running',
        )

        second = self.client.post('/api/investigation/boards/open_case_board/', {'case_id': self.case.id}, format='json')
        self.assertEqual(second.status_code, 200)
        self.assertGreater(len(second.data['board']['nodes']), initial_count)
        labels = [n['label'] for n in second.data['board']['nodes']]
        self.assertTrue(any('Witness: Witness clip' == lbl for lbl in labels))


class SuspectSubmissionFlowTests(APITestCase):
    def setUp(self):
        self.detective = User.objects.create_user(
            username='det_submit', password='Strong12345', email='detsubmit@example.com',
            phone='09136666666', national_id='3666'
        )
        self.sergeant = User.objects.create_user(
            username='serg_submit', password='Strong12345', email='sergsubmit@example.com',
            phone='09137777777', national_id='3777'
        )

        d_role = Role.objects.create(name='detective_submit_role')
        RolePermission.objects.create(role=d_role, action='investigation.board.manage')
        RolePermission.objects.create(role=d_role, action='suspect.manage')
        UserRole.objects.create(user=self.detective, role=d_role)

        s_role = Role.objects.create(name='sergeant_submit_role')
        RolePermission.objects.create(role=s_role, action='suspect.manage')
        RolePermission.objects.create(role=s_role, action='case.read_all')
        UserRole.objects.create(user=self.sergeant, role=s_role)

        self.case = Case.objects.create(
            title='Case submission', description='desc', source=Case.Source.SCENE,
            status=Case.Status.INVESTIGATING, severity=Case.Severity.LEVEL_2,
            created_by=self.detective, assigned_detective=self.detective,
        )

        self.client.force_authenticate(self.detective)
        s1 = self.client.post('/api/investigation/suspects/', {'case': self.case.id, 'full_name': 'Sus One'}, format='json').data
        s2 = self.client.post('/api/investigation/suspects/', {'case': self.case.id, 'full_name': 'Sus Two'}, format='json').data
        self.suspect_ids = [s1['id'], s2['id']]

    def test_detective_submit_and_sergeant_approve(self):
        sub = self.client.post('/api/investigation/suspect-submissions/submit_main_suspects/', {
            'case_id': self.case.id,
            'suspect_ids': self.suspect_ids,
            'detective_reason': 'Connected evidence and witness statements.',
        }, format='json')
        self.assertEqual(sub.status_code, 201)

        self.client.force_authenticate(self.sergeant)
        reviewed = self.client.post(f"/api/investigation/suspect-submissions/{sub.data['id']}/sergeant_review/", {
            'approved': True,
            'message': 'Approved. Start arrests.',
        }, format='json')
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(reviewed.data['status'], 'approved')

    def test_sergeant_reject_notifies_detective(self):
        sub = self.client.post('/api/investigation/suspect-submissions/submit_main_suspects/', {
            'case_id': self.case.id,
            'suspect_ids': self.suspect_ids,
            'detective_reason': 'Need review',
        }, format='json').data

        self.client.force_authenticate(self.sergeant)
        reviewed = self.client.post(f"/api/investigation/suspect-submissions/{sub['id']}/sergeant_review/", {
            'approved': False,
            'message': 'Insufficient match with suspect records.',
        }, format='json')
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(reviewed.data['status'], 'rejected')
