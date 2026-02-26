import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = 'Ensure one superuser exists from environment values without crashing on unique conflicts.'

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin').strip()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'Admin12345!').strip()
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com').strip()
        phone = os.getenv('DJANGO_SUPERUSER_PHONE', '09120000000').strip()
        national_id = os.getenv('DJANGO_SUPERUSER_NATIONAL_ID', '1000000000').strip()

        # First preference: exact username.
        user = User.objects.filter(username=username).first()

        # Fallback: any user with one of unique identifiers.
        if not user:
            user = User.objects.filter(
                Q(national_id=national_id) | Q(email=email) | Q(phone=phone)
            ).first()

        if user:
            changed = False
            # Keep existing unique fields if they differ to avoid creating collisions.
            if not user.is_superuser:
                user.is_superuser = True
                changed = True
            if not user.is_staff:
                user.is_staff = True
                changed = True
            user.set_password(password)
            changed = True
            if changed:
                user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser ready (existing): {user.username}'))
            return

        user = User.objects.create_superuser(
            username=username,
            password=password,
            email=email,
            phone=phone,
            national_id=national_id,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser created: {user.username}'))
