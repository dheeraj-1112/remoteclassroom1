# Initial schema for Remote Classroom.
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("student", "Student"), ("faculty", "Faculty")], default="student", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Subject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140)),
                ("code", models.CharField(max_length=30, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("faculty", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="teaching_subjects", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enrolled_at", models.DateTimeField(auto_now_add=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to=settings.AUTH_USER_MODEL)),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="classroom.subject")),
            ],
            options={"ordering": ["-enrolled_at"]},
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(fields=("student", "subject"), name="unique_student_subject_enrollment"),
        ),
        migrations.CreateModel(
            name="Lecture",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("topic", models.CharField(blank=True, max_length=180)),
                ("description", models.TextField(blank=True)),
                ("video", models.FileField(upload_to="lectures/source/%Y/%m/", validators=[FileExtensionValidator(allowed_extensions=["mp4", "mov", "mkv", "webm", "avi"])])),
                ("duration_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("hls_master_key", models.CharField(blank=True, max_length=500)),
                ("hls_status", models.CharField(choices=[("waiting", "Waiting"), ("processing", "Processing"), ("ready", "Ready"), ("failed", "Failed"), ("skipped", "Skipped on free hosting")], default="waiting", max_length=16)),
                ("transcript", models.TextField(blank=True)),
                ("summary", models.TextField(blank=True)),
                ("summary_word_count", models.PositiveIntegerField(default=0)),
                ("summary_status", models.CharField(choices=[("waiting", "Waiting"), ("processing", "Processing"), ("ready", "Ready"), ("failed", "Failed"), ("skipped", "Skipped on free hosting")], default="waiting", max_length=16)),
                ("summary_error", models.TextField(blank=True)),
                ("transcription_language", models.CharField(blank=True, max_length=16)),
                ("summary_generated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("faculty", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_lectures", to=settings.AUTH_USER_MODEL)),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lectures", to="classroom.subject")),
            ],
            options={"ordering": ["-created_at"], "indexes": [models.Index(fields=["subject", "created_at"], name="lecture_subject_date_idx"), models.Index(fields=["summary_status"], name="lecture_summary_status_idx")]},
        ),
        migrations.CreateModel(
            name="LiveClass",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("starts_at", models.DateTimeField()),
                ("meeting_url", models.URLField(help_text="Paste the Google Meet or Zoom link for this class.", max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("faculty", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="scheduled_live_classes", to=settings.AUTH_USER_MODEL)),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="live_classes", to="classroom.subject")),
            ],
            options={"ordering": ["starts_at"], "indexes": [models.Index(fields=["subject", "starts_at"], name="live_subject_start_idx")]},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("message", models.TextField(max_length=1000)),
                ("link", models.CharField(blank=True, max_length=500)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "indexes": [models.Index(fields=["user", "is_read", "created_at"], name="notification_user_read_idx")]},
        ),
    ]
