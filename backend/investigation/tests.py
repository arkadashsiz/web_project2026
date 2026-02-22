from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from cases.models import Case
from evidence.models import WitnessEvidence
from investigation.models import Interrogation, Suspect, SuspectSubmission
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

    def test_non_assigned_detective_cannot_add_suspect(self):
        other = User.objects.create_user(
            username='det_other_add',
            password='Strong12345',
            email='detotheradd@example.com',
            phone='09139990000',
            national_id='3999',
        )
        d_role2 = Role.objects.create(name='detective_add_role')
        RolePermission.objects.create(role=d_role2, action='suspect.manage')
        RolePermission.objects.create(role=d_role2, action='investigation.board.manage')
        UserRole.objects.create(user=other, role=d_role2)

        self.client.force_authenticate(other)
        resp = self.client.post('/api/investigation/suspects/', {
            'case': self.case.id,
            'full_name': 'Blocked Suspect',
        }, format='json')
        self.assertEqual(resp.status_code, 403)


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


class InterrogationFlowTests(APITestCase):
    def setUp(self):
        self.detective = User.objects.create_user(
            username='det_int', password='Strong12345', email='detint@example.com',
            phone='09138880000', national_id='3888'
        )
        self.sergeant = User.objects.create_user(
            username='ser_int', password='Strong12345', email='serint@example.com',
            phone='09138881111', national_id='3889'
        )
        self.captain = User.objects.create_user(
            username='cap_int', password='Strong12345', email='capint@example.com',
            phone='09138882222', national_id='3890'
        )
        self.chief = User.objects.create_user(
            username='chief_int', password='Strong12345', email='chiefint@example.com',
            phone='09138883333', national_id='3891'
        )
        self.other_detective = User.objects.create_user(
            username='det_other_int', password='Strong12345', email='detotherint@example.com',
            phone='09138884444', national_id='3892'
        )
        self.other_sergeant = User.objects.create_user(
            username='ser_other_int', password='Strong12345', email='serotherint@example.com',
            phone='09138885555', national_id='3893'
        )

        d_role = Role.objects.create(name='det_int_role')
        RolePermission.objects.create(role=d_role, action='interrogation.manage')
        RolePermission.objects.create(role=d_role, action='investigation.board.manage')
        UserRole.objects.create(user=self.detective, role=d_role)
        UserRole.objects.create(user=self.other_detective, role=d_role)

        s_role = Role.objects.create(name='ser_int_role')
        RolePermission.objects.create(role=s_role, action='interrogation.manage')
        RolePermission.objects.create(role=s_role, action='suspect.manage')
        UserRole.objects.create(user=self.sergeant, role=s_role)
        UserRole.objects.create(user=self.other_sergeant, role=s_role)

        c_role = Role.objects.create(name='cap_int_role')
        RolePermission.objects.create(role=c_role, action='interrogation.captain_decision')
        UserRole.objects.create(user=self.captain, role=c_role)

        ch_role = Role.objects.create(name='chief_int_role')
        RolePermission.objects.create(role=ch_role, action='interrogation.chief_review')
        UserRole.objects.create(user=self.chief, role=ch_role)

        self.case = Case.objects.create(
            title='Interrogation Case', description='desc', source=Case.Source.SCENE,
            status=Case.Status.INVESTIGATING, severity=Case.Severity.CRITICAL,
            created_by=self.detective, assigned_detective=self.detective
        )
        self.suspect = Suspect.objects.create(case=self.case, full_name='Sus Inter', status=Suspect.Status.ARRESTED)
        self.submission = SuspectSubmission.objects.create(
            case=self.case,
            detective=self.detective,
            detective_reason='main suspect selected',
            status=SuspectSubmission.Status.APPROVED,
            sergeant=self.sergeant,
        )
        self.submission.suspects.set([self.suspect])

    def test_detective_sergeant_captain_chief_flow(self):
        self.client.force_authenticate(self.detective)
        r1 = self.client.post('/api/investigation/interrogations/record_assessment/', {
            'case_id': self.case.id,
            'suspect_id': self.suspect.id,
            'transcription': 'Q&A transcript',
            'key_values': {'alibi': 'weak'},
            'detective_score': 8,
            'detective_note': 'Strong contradictions',
        }, format='json')
        self.assertEqual(r1.status_code, 200)

        self.client.force_authenticate(self.sergeant)
        r2 = self.client.post('/api/investigation/interrogations/record_assessment/', {
            'case_id': self.case.id,
            'suspect_id': self.suspect.id,
            'sergeant_score': 7,
            'sergeant_note': 'Likely involved',
        }, format='json')
        self.assertEqual(r2.status_code, 200)

        interrogation_id = r2.data['id']
        self.client.force_authenticate(self.captain)
        c = self.client.post(f'/api/investigation/interrogations/{interrogation_id}/captain_decision/', {
            'approved': True,
            'captain_score': 9,
            'captain_note': 'Evidence supports prosecution',
        }, format='json')
        self.assertEqual(c.status_code, 200)
        self.assertEqual(c.data['chief_decision'], Interrogation.ChiefDecision.PENDING)
        self.assertEqual(c.data['captain_outcome'], Interrogation.CaptainOutcome.APPROVED)

        self.client.force_authenticate(self.chief)
        ch = self.client.post(f'/api/investigation/interrogations/{interrogation_id}/chief_review/', {
            'approved': True,
            'chief_note': 'Approved',
        }, format='json')
        self.assertEqual(ch.status_code, 200)
        self.assertEqual(ch.data['chief_decision'], Interrogation.ChiefDecision.APPROVED)

        self.case.refresh_from_db()
        self.assertEqual(self.case.status, Case.Status.SENT_TO_COURT)

    def test_only_case_detective_and_case_sergeant_can_score(self):
        self.client.force_authenticate(self.detective)
        created = self.client.post('/api/investigation/interrogations/record_assessment/', {
            'case_id': self.case.id,
            'suspect_id': self.suspect.id,
            'detective_score': 8,
            'detective_note': 'case detective input',
        }, format='json')
        self.assertEqual(created.status_code, 200)

        # Other detective cannot score this case.
        self.client.force_authenticate(self.other_detective)
        denied_det = self.client.post('/api/investigation/interrogations/record_assessment/', {
            'case_id': self.case.id,
            'suspect_id': self.suspect.id,
            'detective_score': 6,
        }, format='json')
        self.assertEqual(denied_det.status_code, 403)

        # Other sergeant cannot score this case (not case sergeant reviewer).
        self.client.force_authenticate(self.other_sergeant)
        denied_ser = self.client.post('/api/investigation/interrogations/record_assessment/', {
            'case_id': self.case.id,
            'suspect_id': self.suspect.id,
            'sergeant_score': 6,
        }, format='json')
        self.assertEqual(denied_ser.status_code, 403)

    def test_captain_can_reject_trial_and_keep_case_investigating(self):
        self.client.force_authenticate(self.detective)
        self.client.post('/api/investigation/interrogations/record_assessment/', {
            'case_id': self.case.id,
            'suspect_id': self.suspect.id,
            'detective_score': 8,
        }, format='json')
        self.client.force_authenticate(self.sergeant)
        scored = self.client.post('/api/investigation/interrogations/record_assessment/', {
            'case_id': self.case.id,
            'suspect_id': self.suspect.id,
            'sergeant_score': 7,
        }, format='json')
        iid = scored.data['id']

        self.client.force_authenticate(self.captain)
        rej = self.client.post(f'/api/investigation/interrogations/{iid}/captain_decision/', {
            'approved': False,
            'captain_score': 5,
            'captain_note': 'Need more evidence',
        }, format='json')
        self.assertEqual(rej.status_code, 200)
        self.assertEqual(rej.data['captain_outcome'], Interrogation.CaptainOutcome.REJECTED)

        self.case.refresh_from_db()
        self.assertEqual(self.case.status, Case.Status.INVESTIGATING)


class HighAlertRankingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='high_alert_user',
            password='Strong12345',
            email='ha@example.com',
            phone='09131112222',
            national_id='5001',
        )
        self.client.force_authenticate(self.user)

    def test_high_alert_formula_and_sorting(self):
        # Person A => Lj=40, Di=4 => score=160, reward=3,200,000,000
        case_a_open = Case.objects.create(
            title='A-open',
            description='x',
            source=Case.Source.SCENE,
            status=Case.Status.OPEN,
            severity=Case.Severity.CRITICAL,
            created_by=self.user,
        )
        a = Suspect.objects.create(case=case_a_open, full_name='Person A', national_id='A001', status=Suspect.Status.WANTED)
        a.marked_at = timezone.now() - timezone.timedelta(days=40)
        a.save(update_fields=['marked_at'])

        # Person B => Lj=31, Di=2 => score=62
        case_b_open = Case.objects.create(
            title='B-open',
            description='x',
            source=Case.Source.SCENE,
            status=Case.Status.OPEN,
            severity=Case.Severity.LEVEL_2,
            created_by=self.user,
        )
        b = Suspect.objects.create(case=case_b_open, full_name='Person B', national_id='B001', status=Suspect.Status.WANTED)
        b.marked_at = timezone.now() - timezone.timedelta(days=31)
        b.save(update_fields=['marked_at'])

        # Person C not high-alert => Lj=10
        case_c_open = Case.objects.create(
            title='C-open',
            description='x',
            source=Case.Source.SCENE,
            status=Case.Status.OPEN,
            severity=Case.Severity.LEVEL_1,
            created_by=self.user,
        )
        c = Suspect.objects.create(case=case_c_open, full_name='Person C', national_id='C001', status=Suspect.Status.WANTED)
        c.marked_at = timezone.now() - timezone.timedelta(days=10)
        c.save(update_fields=['marked_at'])

        resp = self.client.get('/api/investigation/high-alert/')
        self.assertEqual(resp.status_code, 200)
        rows = resp.data
        self.assertEqual(len(rows), 2)
        self.assertGreaterEqual(rows[0]['rank_score'], rows[1]['rank_score'])
        self.assertEqual(rows[0]['full_name'], 'Person A')
        self.assertEqual(rows[0]['rank_score'], 160)
        self.assertEqual(rows[0]['reward_irr'], 3_200_000_000)

    def test_superuser_can_create_wanted_profile(self):
        su = User.objects.create_superuser(
            username='root_high_alert',
            password='Strong12345',
            email='rootha@example.com',
            phone='09139991111',
            national_id='7001',
        )
        self.client.force_authenticate(su)
        resp = self.client.post('/api/investigation/suspects/create_wanted_profile/', {
            'full_name': 'Seed Wanted User',
            'national_id': 'SEED-HA-1',
            'severity': 4,
            'days_wanted': 45,
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        sid = resp.data['suspect']['id']
        s = Suspect.objects.get(id=sid)
        self.assertEqual(s.status, Suspect.Status.WANTED)
        self.assertGreaterEqual(s.days_wanted(), 44)

    def test_non_superuser_cannot_create_wanted_profile(self):
        normal = User.objects.create_user(
            username='normal_high_alert',
            password='Strong12345',
            email='normalha@example.com',
            phone='09139992222',
            national_id='7002',
        )
        self.client.force_authenticate(normal)
        resp = self.client.post('/api/investigation/suspects/create_wanted_profile/', {
            'full_name': 'Blocked User',
            'severity': 2,
            'days_wanted': 31,
        }, format='json')
        self.assertEqual(resp.status_code, 403)
