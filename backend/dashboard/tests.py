from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class DashboardEndpointsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='u1', password='Strong12345', email='x@example.com', phone='09121111111', national_id='1111'
        )
        self.client.force_authenticate(self.user)

    def test_stats_endpoint(self):
        resp = self.client.get('/api/dashboard/stats/')
        self.assertEqual(resp.status_code, 200)

    def test_modules_endpoint(self):
        resp = self.client.get('/api/dashboard/modules/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('modules', resp.data)
