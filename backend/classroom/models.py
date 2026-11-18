from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        FACULTY = "faculty", "Faculty"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Subject(models.Model):
    name = models.CharField(max_length=140)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="teaching_subjects")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "subject"], name="unique_student_subject_enrollment")]
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student.username} → {self.subject.code}"


class Lecture(models.Model):
    class ProcessingStatus(models.TextChoices):
        WAITING = "waiting", "Waiting"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped on free hosting"

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="lectures")
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_lectures")
    title = models.CharField(max_length=180)
    topic = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    video = models.FileField(
        upload_to="lectures/source/%Y/%m/",
        validators=[FileExtensionValidator(allowed_extensions=["mp4", "mov", "mkv", "webm", "avi"])],
    )
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    hls_master_key = models.CharField(max_length=500, blank=True)
    hls_status = models.CharField(max_length=16, choices=ProcessingStatus.choices, default=ProcessingStatus.WAITING)
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    summary_word_count = models.PositiveIntegerField(default=0)
    summary_status = models.CharField(max_length=16, choices=ProcessingStatus.choices, default=ProcessingStatus.WAITING)
    summary_error = models.TextField(blank=True)
    transcription_language = models.CharField(max_length=16, blank=True)
    summary_generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["subject", "created_at"], name="lecture_subject_date_idx"),
            models.Index(fields=["summary_status"], name="lecture_summary_status_idx"),
        ]

    def __str__(self):
        return self.title

    @property
    def is_ready_for_students(self):
        return bool(self.video)


class LiveClass(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="live_classes")
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="scheduled_live_classes")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    meeting_url = models.URLField(max_length=500, help_text="Paste the Google Meet or Zoom link for this class.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [models.Index(fields=["subject", "starts_at"], name="live_subject_start_idx")]

    def __str__(self):
        return f"{self.title} — {self.starts_at:%Y-%m-%d %H:%M}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=180)
    message = models.TextField(max_length=1000)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "created_at"], name="notification_user_read_idx")]

    def __str__(self):
        return f"{self.user.username}: {self.title}"
