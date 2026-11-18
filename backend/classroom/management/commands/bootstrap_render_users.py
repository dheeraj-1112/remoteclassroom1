import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from classroom.models import Profile


class Command(BaseCommand):
    help = "Create optional initial faculty/admin users from Render environment variables."

    def handle(self, *args, **options):
        User = get_user_model()
        self._create_role_user(
            User,
            prefix="BOOTSTRAP_FACULTY",
            role=Profile.Role.FACULTY,
            is_staff=False,
            is_superuser=False,
        )
        self._create_role_user(
            User,
            prefix="BOOTSTRAP_ADMIN",
            role=Profile.Role.FACULTY,
            is_staff=True,
            is_superuser=True,
        )

    def _create_role_user(self, User, prefix, role, is_staff, is_superuser):
        username = os.getenv(f"{prefix}_USERNAME", "").strip()
        password = os.getenv(f"{prefix}_PASSWORD", "")
        email = os.getenv(f"{prefix}_EMAIL", "").strip()
        if not username and not password:
            return
        if not username or not password:
            self.stderr.write(self.style.WARNING(f"{prefix}: username or password missing; skipped."))
            return
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": is_staff, "is_superuser": is_superuser},
        )
        if created:
            user.set_password(password)
            user.email = email
            user.is_active = True
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            Profile.objects.update_or_create(user=user, defaults={"role": role})
            self.stdout.write(self.style.SUCCESS(f"Created {prefix.lower()} account: {username}"))
        else:
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            if email and not user.email:
                user.email = email
            user.save(update_fields=["is_staff", "is_superuser", "email"])
            Profile.objects.update_or_create(user=user, defaults={"role": role})
            self.stdout.write(f"{prefix}: account {username} already exists; password was not changed.")
