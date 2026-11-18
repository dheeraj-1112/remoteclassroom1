from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Enrollment, Lecture, LiveClass, Notification, Profile, Subject

User = get_user_model()

class AuthAndClassroomAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.faculty = User.objects.create_user(username="faculty1", password="StrongPass123", email="faculty@example.test")
        Profile.objects.update_or_create(user=self.faculty, defaults={"role": Profile.Role.FACULTY})
        self.student = User.objects.create_user(username="student1", password="StrongPass123", email="student@example.test")
        Profile.objects.update_or_create(user=self.student, defaults={"role": Profile.Role.STUDENT})
        self.subject = Subject.objects.create(code="CSE101", name="Computer Science", faculty=self.faculty)

    def test_student_can_login_and_enroll(self):
        response = self.client.post("/api/auth/login/", {"username": "student1", "password": "StrongPass123"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        enroll = self.client.post(f"/api/subjects/{self.subject.id}/enroll/")
        self.assertEqual(enroll.status_code, 201)
        self.assertTrue(Enrollment.objects.filter(student=self.student, subject=self.subject).exists())

    def test_student_cannot_create_subject(self):
        self.client.force_authenticate(self.student)
        response = self.client.post("/api/subjects/", {"code": "CSE102", "name": "Networks"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_faculty_can_create_subject(self):
        self.client.force_authenticate(self.faculty)
        response = self.client.post("/api/subjects/", {"code": "CSE102", "name": "Networks"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["faculty"], self.faculty.id)

    def test_student_cannot_read_lecture_without_enrollment(self):
        lecture = Lecture.objects.create(
            subject=self.subject,
            faculty=self.faculty,
            title="Private lecture",
            video=SimpleUploadedFile("private.mp4", b"not-a-real-video", content_type="video/mp4"),
        )
        self.client.force_authenticate(self.student)
        response = self.client.get(f"/api/lectures/{lecture.id}/")
        self.assertEqual(response.status_code, 404)

    def test_student_registration_is_student_role(self):
        response = self.client.post("/api/auth/register/", {
            "username": "newstudent",
            "email": "newstudent@example.test",
            "password": "Valid-Strong-Pass-938!",
            "first_name": "New",
            "last_name": "Student",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["role"], Profile.Role.STUDENT)

    def test_student_cannot_trigger_summary_regeneration(self):
        Enrollment.objects.create(student=self.student, subject=self.subject)
        lecture = Lecture.objects.create(
            subject=self.subject,
            faculty=self.faculty,
            title="Lecture for retry permission test",
            video=SimpleUploadedFile("retry.mp4", b"not-a-real-video", content_type="video/mp4"),
        )
        self.client.force_authenticate(self.student)
        response = self.client.post(f"/api/lectures/{lecture.id}/regenerate_summary/")
        self.assertEqual(response.status_code, 403)

    def test_scheduling_live_class_notifies_enrolled_students(self):
        Enrollment.objects.create(student=self.student, subject=self.subject)
        self.client.force_authenticate(self.faculty)
        response = self.client.post("/api/live-classes/", {
            "subject": self.subject.id,
            "title": "Revision class",
            "description": "Unit revision",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "meeting_url": "https://meet.google.com/abc-defg-hij",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Notification.objects.filter(user=self.student, title="New live class scheduled").exists())

