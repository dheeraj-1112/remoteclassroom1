import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from classroom.models import Enrollment, Profile, Subject

User = get_user_model()

class Command(BaseCommand):
    help = "Create local demonstration faculty/student accounts and one subject. Use only for a development demo."

    def handle(self, *args, **options):
        from django.conf import settings
        if not settings.DEBUG:
            raise CommandError("seed_demo is disabled when DEBUG is false.")
        password = os.getenv("DEMO_PASSWORD", "DemoOnlyChange123!")
        faculty, _ = User.objects.get_or_create(
            username="faculty.demo",
            defaults={"email": "faculty.demo@example.test", "first_name": "Demo", "last_name": "Faculty"},
        )
        faculty.set_password(password)
        faculty.save()
        Profile.objects.update_or_create(user=faculty, defaults={"role": Profile.Role.FACULTY})

        student, _ = User.objects.get_or_create(
            username="student.demo",
            defaults={"email": "student.demo@example.test", "first_name": "Demo", "last_name": "Student"},
        )
        student.set_password(password)
        student.save()
        Profile.objects.update_or_create(user=student, defaults={"role": Profile.Role.STUDENT})

        subject, _ = Subject.objects.get_or_create(
            code="CSE-RC101",
            defaults={"name": "Remote Classroom Demo", "description": "Sample subject for testing lecture uploads and class schedules.", "faculty": faculty},
        )
        Enrollment.objects.get_or_create(student=student, subject=subject)
        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write(f"Faculty username: faculty.demo")
        self.stdout.write(f"Student username: student.demo")
        self.stdout.write(f"Password for both: {password}")
        self.stdout.write("Change or delete these accounts before deploying a public instance.")
