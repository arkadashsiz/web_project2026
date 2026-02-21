from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    national_id = models.CharField(max_length=20, unique=True)

    REQUIRED_FIELDS = ['email', 'phone', 'national_id']

    def __str__(self):
        return f"{self.username} ({self.national_id})"
