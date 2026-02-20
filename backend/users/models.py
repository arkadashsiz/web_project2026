from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # 10 = Cadet, 20 = Officer, 40 = Detective, 60 = Sergeant, 80 = Captain, 100 = Chief
    access_level = models.PositiveIntegerField(
        default=10, 
        help_text="Higher number = Higher Authority. Used for permission checks."
    )

    def __str__(self):
        return f"{self.name} (Level {self.access_level})"
    

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    national_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    
    role = models.ForeignKey(
        Role, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="personnel"
    )

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS=[
        "email",
        "phone_number",
        "national_id",
        "first_name",
        "last_name",
    ]

    def __str__(self):
        role_name = self.role.name if self.role else "Civilian/Unassigned"
        return f"{self.last_name}, {self.first_name} - {role_name}"
