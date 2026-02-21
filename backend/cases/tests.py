from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from cases.models import CaseComplainant, ComplaintSubmission
from rbac.models import Role, RolePermission, UserRole

User = get_user_model()


class CasesFlowTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='complainant',
            password='VeryStrong123',
            email='c@example.com',
            phone='09123333333',
            national_id='111',
        )
        self.client.force_authenticate(user=self.user)
        complainant_role = Role.objects.create(name='complainant')
        RolePermission.objects.create(role=complainant_role, action='case.submit_complaint')
        UserRole.objects.create(user=self.user, role=complainant_role)

    def test_submit_complaint(self):
        resp = self.client.post('/api/cases/cases/submit_complaint/', {
            'title': 'Phone theft',
            'description': 'Lost phone in street',
            'severity': 1,
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['source'], 'complaint')

    def test_intern_review_reject_three_times_void(self):
        case = self.client.post('/api/cases/cases/submit_complaint/', {
            'title': 'Complaint', 'description': 'desc', 'severity': 1,
        }, format='json').data
        cid = case['id']

        role = Role.objects.create(name='cadet')
        RolePermission.objects.create(role=role, action='case.complaint.intern_review')
        UserRole.objects.create(user=self.user, role=role)

        for _ in range(3):
            self.client.post(f'/api/cases/cases/{cid}/intern_review/', {'approved': False, 'note': 'missing'}, format='json')
            if _ < 2:
                self.client.post(
                    f'/api/cases/cases/{cid}/resubmit_complaint/',
                    {'title': 'Complaint', 'description': 'desc'},
                    format='json',
                )

        detail = self.client.get(f'/api/cases/cases/{cid}/').data
        self.assertEqual(detail['status'], 'void')

    def test_scene_report_requires_permission(self):
        resp = self.client.post('/api/cases/cases/submit_scene_report/', {
            'title': 'Scene', 'description': 'desc', 'severity': 2,
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_scene_report_success_with_permission(self):
        role = Role.objects.create(name='officer')
        RolePermission.objects.create(role=role, action='case.scene.create')
        UserRole.objects.create(user=self.user, role=role)

        resp = self.client.post('/api/cases/cases/submit_scene_report/', {
            'title': 'Scene',
            'description': 'desc',
            'severity': 2,
            'witnesses': [
                {'full_name': 'Ali', 'national_id': '445', 'phone': '09128888888', 'statement': 'seen suspect'}
            ]
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['status'], 'under_review')

    def test_assign_detective_requires_permission(self):
        case = self.client.post('/api/cases/cases/submit_complaint/', {
            'title': 'Phone theft', 'description': 'x', 'severity': 1,
        }, format='json').data

        resp = self.client.post(f"/api/cases/cases/{case['id']}/assign_detective/", {'detective_id': self.user.id}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_cadet_reject_must_have_error_message(self):
        case = self.client.post('/api/cases/cases/submit_complaint/', {
            'title': 'Complaint', 'description': 'desc', 'severity': 1,
        }, format='json').data
        cid = case['id']

        role = Role.objects.create(name='cadet_err')
        RolePermission.objects.create(role=role, action='case.complaint.intern_review')
        UserRole.objects.create(user=self.user, role=role)

        resp = self.client.post(f'/api/cases/cases/{cid}/intern_review/', {'approved': False, 'note': ''}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_officer_reject_returns_case_to_cadet_not_complainant(self):
        case = self.client.post('/api/cases/cases/submit_complaint/', {
            'title': 'Complaint', 'description': 'desc', 'severity': 1,
        }, format='json').data
        cid = case['id']

        cadet_role = Role.objects.create(name='cadet2')
        RolePermission.objects.create(role=cadet_role, action='case.complaint.intern_review')
        officer_role = Role.objects.create(name='officer2')
        RolePermission.objects.create(role=officer_role, action='case.complaint.officer_review')
        UserRole.objects.create(user=self.user, role=cadet_role)
        UserRole.objects.create(user=self.user, role=officer_role)

        comp = CaseComplainant.objects.get(case_id=cid, user=self.user)
        self.client.post(
            f'/api/cases/cases/{cid}/intern_review_complainant/',
            {'complainant_id': comp.id, 'approved': True, 'note': 'ok'},
            format='json',
        )
        self.client.post(f'/api/cases/cases/{cid}/intern_review/', {'approved': True, 'note': 'ready'}, format='json')
        resp = self.client.post(f'/api/cases/cases/{cid}/officer_review/', {'approved': False, 'note': 'need recheck'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['stage'], ComplaintSubmission.Stage.RETURNED_TO_CADET)

    def test_complainant_can_resubmit_after_cadet_return(self):
        case = self.client.post('/api/cases/cases/submit_complaint/', {
            'title': 'Complaint', 'description': 'desc', 'severity': 1,
        }, format='json').data
        cid = case['id']

        role = Role.objects.create(name='cadet3')
        RolePermission.objects.create(role=role, action='case.complaint.intern_review')
        UserRole.objects.create(user=self.user, role=role)

        self.client.post(f'/api/cases/cases/{cid}/intern_review/', {'approved': False, 'note': 'missing field'}, format='json')
        resp = self.client.post(
            f'/api/cases/cases/{cid}/resubmit_complaint/',
            {'title': 'Complaint fixed', 'description': 'updated'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['title'], 'Complaint fixed')
