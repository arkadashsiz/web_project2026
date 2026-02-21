from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from cases.models import Case
from rbac.models import Role, RolePermission, UserRole

User = get_user_model()


class EvidenceFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='evi_user',
            password='Strong12345',
            email='evi@example.com',
            phone='09132222222',
            national_id='3222',
        )
        role = Role.objects.create(name='evidence officer')
        RolePermission.objects.create(role=role, action='evidence.manage')
        UserRole.objects.create(user=self.user, role=role)
        self.client.force_authenticate(self.user)

        self.case = Case.objects.create(
            title='Evidence Case',
            description='desc',
            source=Case.Source.SCENE,
            status=Case.Status.OPEN,
            severity=Case.Severity.LEVEL_2,
            created_by=self.user,
        )

    def test_witness_evidence_requires_transcript_or_media(self):
        resp = self.client.post('/api/evidence/witness/', {
            'case': self.case.id,
            'title': 'Witness file',
            'description': 'desc',
            'transcript': '',
            'media_items': [],
            'media_url': '',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_witness_evidence_with_media_items(self):
        resp = self.client.post('/api/evidence/witness/', {
            'case': self.case.id,
            'title': 'Witness media',
            'description': 'desc',
            'media_items': [{'type': 'video', 'url': 'https://example.com/v.mp4'}],
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_biological_requires_images(self):
        resp = self.client.post('/api/evidence/biological/', {
            'case': self.case.id,
            'title': 'Blood sample',
            'description': 'possible blood',
            'image_urls': [],
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_vehicle_xor_plate_serial(self):
        resp = self.client.post('/api/evidence/vehicle/', {
            'case': self.case.id,
            'title': 'Vehicle',
            'description': 'suspected car',
            'model_name': 'Sedan',
            'color': 'Black',
            'plate_number': '12A34567',
            'serial_number': 'SN1',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_identification_accepts_empty_metadata(self):
        resp = self.client.post('/api/evidence/identification/', {
            'case': self.case.id,
            'title': 'ID card',
            'description': 'found near scene',
            'owner_full_name': 'Unknown Person',
            'metadata': {},
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_biological_results_can_be_updated_later(self):
        created = self.client.post('/api/evidence/biological/', {
            'case': self.case.id,
            'title': 'Hair sample',
            'description': 'collected from scene',
            'image_urls': ['https://example.com/hair.jpg'],
        }, format='json')
        self.assertEqual(created.status_code, 201)
        evidence_id = created.data['id']

        # evidence manager cannot update forensic results
        denied = self.client.post(f'/api/evidence/biological/{evidence_id}/update_results/', {
            'forensic_result': 'DNA matched with suspect #12',
            'identity_db_result': 'Fingerprint record found in national DB',
        }, format='json')
        self.assertEqual(denied.status_code, 403)

        # forensic/coroner can update
        forensic = User.objects.create_user(
            username='forensic_user',
            password='Strong12345',
            email='forensic@example.com',
            phone='09133333333',
            national_id='3333',
        )
        coroner_role = Role.objects.create(name='coroner')
        RolePermission.objects.create(role=coroner_role, action='evidence.biological.review')
        UserRole.objects.create(user=forensic, role=coroner_role)
        self.client.force_authenticate(forensic)

        updated = self.client.post(f'/api/evidence/biological/{evidence_id}/update_results/', {
            'forensic_result': 'DNA matched with suspect #12',
            'identity_db_result': 'Fingerprint record found in national DB',
        }, format='json')
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data['forensic_result'], 'DNA matched with suspect #12')
        self.assertEqual(updated.data['identity_db_result'], 'Fingerprint record found in national DB')

    def test_biological_cannot_be_created_with_results(self):
        resp = self.client.post('/api/evidence/biological/', {
            'case': self.case.id,
            'title': 'Blood sample',
            'description': 'found',
            'image_urls': ['https://example.com/blood.jpg'],
            'forensic_result': 'should not be here',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
