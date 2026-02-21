from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Q
from django.utils import timezone


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Role Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    # For managing hierarchy (e.g., Chief > Captain > Sergeant)
    access_level = models.PositiveIntegerField(
        default=10,
        help_text=_("Higher number = Higher Authority. Used for hierarchy and permission checks.")
    )

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ['-access_level']  # Highest authority first

    def __str__(self):
        return f"{self.name} (Level {self.access_level})"


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name=_("Email Address"))
    phone_number = models.CharField(max_length=15, unique=True, verbose_name=_("Phone Number"))
    national_id = models.CharField(max_length=10, unique=True, verbose_name=_("National ID"))

    # Force required
    first_name = models.CharField(max_length=150, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=150, verbose_name=_("Last Name"))

    roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name="users",
        verbose_name=_("Roles")
    )

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = [
        "email",
        "phone_number",
        "national_id",
        "first_name",
        "last_name",
    ]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.first_name} {self.last_name} - ({self.username})"

    @property
    def highest_access_level(self) -> int:
        aggregate = self.roles.aggregate(max_level=models.Max('access_level'))
        return aggregate['max_level'] or 0

    @property
    def is_police(self) -> bool:
        """
        Police personnel are anyone with access level >= 10.
        """
        return self.highest_access_level >= 10

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(name__iexact=role_name).exists()


class RoleRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='role_requests')
    requested_role = models.ForeignKey('Role', on_delete=models.CASCADE, related_name='requests')
    reason = models.TextField(help_text="Why do you need this role?", blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_role_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'requested_role'],
                condition=Q(status='pending'),
                name='unique_pending_role_request'
            )
        ]

    def __str__(self):
        return f"{self.user.username} requests {self.requested_role.name} - {self.status}"
