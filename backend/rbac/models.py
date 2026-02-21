from django.conf import settings
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    action = models.CharField(max_length=120)

    class Meta:
        unique_together = ('role', 'action')

    def __str__(self):
        return f'{self.role.name}:{self.action}'


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f'{self.user.username}:{self.role.name}'
