from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from rbac.models import Role, UserRole

User = get_user_model()


class RBACRoleDeleteTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='rbac_admin',
            password='Strong12345',
            email='rbac_admin@example.com',
            phone='09120001111',
            national_id='9000000001',
        )
        self.user1 = User.objects.create_user(
            username='rbac_u1',
            password='Strong12345',
            email='rbac_u1@example.com',
            phone='09120001112',
            national_id='9000000002',
        )
        self.user2 = User.objects.create_user(
            username='rbac_u2',
            password='Strong12345',
            email='rbac_u2@example.com',
            phone='09120001113',
            national_id='9000000003',
        )
        self.role = Role.objects.create(name='temp role')
        UserRole.objects.create(user=self.user1, role=self.role)
        UserRole.objects.create(user=self.user2, role=self.role)
        self.client.force_authenticate(self.admin)

    def test_superuser_delete_role_removes_assignments_for_all_users(self):
        self.assertEqual(UserRole.objects.filter(role=self.role).count(), 2)
        resp = self.client.delete(f'/api/rbac/roles/{self.role.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['removed_user_roles'], 2)
        self.assertFalse(Role.objects.filter(id=self.role.id).exists())
        self.assertEqual(UserRole.objects.filter(role_id=self.role.id).count(), 0)
