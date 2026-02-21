from django.urls import reverse
from rest_framework.test import APITestCase
import importlib.util

HAS_SIMPLEJWT = importlib.util.find_spec('rest_framework_simplejwt') is not None


class AccountsAPITest(APITestCase):
    def test_register_success(self):
        payload = {
            'username': 'user1',
            'password': 'VeryStrong123',
            'email': 'u1@example.com',
            'phone': '09120000001',
            'national_id': '001',
            'first_name': 'U',
            'last_name': 'One',
        }
        resp = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_login_with_username(self):
        self.client.post('/api/auth/register/', {
            'username': 'user2',
            'password': 'VeryStrong123',
            'email': 'u2@example.com',
            'phone': '09120000002',
            'national_id': '002',
        }, format='json')
        resp = self.client.post('/api/auth/login/', {'identifier': 'user2', 'password': 'VeryStrong123'}, format='json')
        expected = 200 if HAS_SIMPLEJWT else 501
        self.assertEqual(resp.status_code, expected)
        if HAS_SIMPLEJWT:
            self.assertIn('access', resp.data)

    def test_login_with_email(self):
        self.client.post('/api/auth/register/', {
            'username': 'user3',
            'password': 'VeryStrong123',
            'email': 'u3@example.com',
            'phone': '09120000003',
            'national_id': '003',
        }, format='json')
        resp = self.client.post('/api/auth/login/', {'identifier': 'u3@example.com', 'password': 'VeryStrong123'}, format='json')
        expected = 200 if HAS_SIMPLEJWT else 501
        self.assertEqual(resp.status_code, expected)

    def test_login_invalid_credentials(self):
        resp = self.client.post('/api/auth/login/', {'identifier': 'x', 'password': 'wrong'}, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_me_endpoint_requires_auth(self):
        resp = self.client.get('/api/auth/me/')
        self.assertIn(resp.status_code, [401, 403])
