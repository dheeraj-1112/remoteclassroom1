import logging
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .models import Enrollment, Lecture, LiveClass, Notification, Profile, Subject
from .permissions import IsFaculty, IsLectureParticipant, IsSubjectFacultyOwner
from .serializers import (
    LectureSerializer, LiveClassSerializer, NotificationSerializer,
    RegisterSerializer, SubjectSerializer, UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def health_check(request):
    return JsonResponse({"status": "ok", "service": "remote-classroom-api", "time": timezone.now().isoformat()})


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Username or password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "This account is inactive. Contact the project administrator."}, status=status.HTTP_403_FORBIDDEN)
        profile, _ = Profile.objects.get_or_create(user=user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(APIView):
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        Profile.objects.get_or_create(user=request.user)
        return Response(UserSerializer(request.user).data)


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        return Subject.objects.select_related("faculty").annotate(lecture_count=Count("lectures")).all()

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated(), IsFaculty(), IsSubjectFacultyOwner()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(faculty=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.faculty_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only modify subjects assigned to your faculty account.")
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        subject = self.get_object()
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if profile.role != Profile.Role.STUDENT:
            return Response({"detail": "Only student accounts can enroll in a subject."}, status=403)
        enrollment, created = Enrollment.objects.get_or_create(student=request.user, subject=subject)
        return Response({"enrolled": True, "created": created, "subject": subject.code}, status=201 if created else 200)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if profile.role == Profile.Role.FACULTY:
            qs = self.get_queryset().filter(faculty=request.user)
        else:
            qs = self.get_queryset().filter(enrollments__student=request.user)
        return Response(self.get_serializer(qs, many=True).data)


class LectureViewSet(viewsets.ModelViewSet):
    serializer_class = LectureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Lecture.objects.select_related("subject", "faculty")
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        if self.request.user.is_staff:
            return qs
        if profile.role == Profile.Role.FACULTY:
            return qs.filter(faculty=self.request.user)
        return qs.filter(subject__enrollments__student=self.request.user).distinct()

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "regenerate_summary", "generate_summary"}:
            return [IsAuthenticated(), IsFaculty(), IsLectureParticipant()]
        return [IsAuthenticated(), IsLectureParticipant()]

    def perform_create(self, serializer):
        subject = serializer.validated_data["subject"]
        if subject.faculty_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only upload lectures for a subject assigned to your faculty account.")
        lecture = serializer.save(faculty=self.request.user)
        if settings.FREE_TIER_MODE and not settings.ENABLE_HLS_PROCESSING:
            lecture.hls_status = Lecture.ProcessingStatus.SKIPPED
            lecture.save(update_fields=["hls_status", "updated_at"])
        self._queue_processing(lecture.id)

    def perform_update(self, serializer):
        subject = serializer.validated_data.get("subject", serializer.instance.subject)
        if subject.faculty_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only assign lectures to subjects owned by your faculty account.")
        video_changed = "video" in serializer.validated_data
        lecture = serializer.save()
        if video_changed:
            lecture.hls_status = (
                Lecture.ProcessingStatus.SKIPPED
                if settings.FREE_TIER_MODE and not settings.ENABLE_HLS_PROCESSING
                else Lecture.ProcessingStatus.WAITING
            )
            lecture.summary_status = Lecture.ProcessingStatus.WAITING
            lecture.hls_master_key = ""
            lecture.transcript = ""
            lecture.summary = ""
            lecture.summary_word_count = 0
            lecture.summary_error = ""
            lecture.save(update_fields=["hls_status", "summary_status", "hls_master_key", "transcript", "summary", "summary_word_count", "summary_error", "updated_at"])
            self._queue_processing(lecture.id)

    @staticmethod
    def _queue_processing(lecture_id):
        # Free Render instances have no free background-worker service and no
        # persistent disk. Keep the uploaded original video in object storage;
        # run Lite Mode transcription as a bounded API action instead.
        if settings.FREE_TIER_MODE:
            updates = {"summary_status": Lecture.ProcessingStatus.WAITING}
            if not settings.ENABLE_HLS_PROCESSING:
                updates["hls_status"] = Lecture.ProcessingStatus.SKIPPED
            Lecture.objects.filter(pk=lecture_id).update(**updates)
            return

        from .tasks import generate_hls, generate_lecture_summary

        def enqueue_after_commit():
            # The callback runs after the DB transaction has committed, so catch broker
            # errors inside the callback rather than around transaction.on_commit().
            try:
                generate_hls.delay(lecture_id)
            except Exception as exc:
                Lecture.objects.filter(pk=lecture_id).update(
                    hls_status=Lecture.ProcessingStatus.FAILED,
                )
                logger.exception("Could not queue HLS processing for lecture %s", lecture_id)
            try:
                generate_lecture_summary.delay(lecture_id)
            except Exception as exc:
                Lecture.objects.filter(pk=lecture_id).update(
                    summary_status=Lecture.ProcessingStatus.FAILED,
                    summary_error=f"Background queue is unavailable: {exc}"[:2000],
                )
                logger.exception("Could not queue summary processing for lecture %s", lecture_id)

        transaction.on_commit(enqueue_after_commit)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsFaculty, IsLectureParticipant],
    )
    def generate_summary(self, request, pk=None):
        """Generate Lite Mode text on the free cloud deployment.

        This deliberately handles only small uploads (25 MB max) so it can run
        without a paid Celery worker. Local/full deployments use the Whisper task.
        """
        if not settings.FREE_TIER_MODE:
            return Response({"detail": "Use the background Whisper worker on the full deployment."}, status=409)
        lecture = self.get_object()
        if lecture.summary_status == Lecture.ProcessingStatus.READY and lecture.summary:
            return Response(self.get_serializer(lecture).data)
        if lecture.summary_status == Lecture.ProcessingStatus.PROCESSING:
            # A request can be interrupted by a free-instance restart or proxy timeout.
            # Allow a retry when the processing marker has clearly become stale.
            if lecture.updated_at and lecture.updated_at >= timezone.now() - timedelta(minutes=10):
                return Response({"detail": "A summary is already being generated."}, status=409)
        if not settings.GROQ_API_KEY:
            lecture.summary_status = Lecture.ProcessingStatus.FAILED
            lecture.summary_error = "Cloud transcription is not configured. Add GROQ_API_KEY in Render environment settings."
            lecture.save(update_fields=["summary_status", "summary_error", "updated_at"])
            return Response({"detail": lecture.summary_error}, status=503)
        if lecture.video.size > 25 * 1024 * 1024:
            lecture.summary_status = Lecture.ProcessingStatus.FAILED
            lecture.summary_error = "The free cloud transcription route accepts files up to 25 MB. Compress the video and upload it again."
            lecture.save(update_fields=["summary_status", "summary_error", "updated_at"])
            return Response({"detail": lecture.summary_error}, status=413)

        lecture.summary_status = Lecture.ProcessingStatus.PROCESSING
        lecture.summary_error = ""
        lecture.save(update_fields=["summary_status", "summary_error", "updated_at"])
        try:
            from .services.groq_transcriber import transcribe_video
            from .services.summarizer import summarize_transcript

            with default_storage.open(lecture.video.name, "rb") as source_file:
                transcript, language = transcribe_video(
                    source_file,
                    lecture.video.name,
                    settings.GROQ_API_KEY,
                    settings.GROQ_WHISPER_MODEL,
                    settings.WHISPER_LANGUAGE,
                )
            summary, count = summarize_transcript(transcript, minimum_words=300, maximum_words=500)
            lecture.transcript = transcript
            lecture.summary = summary
            lecture.summary_word_count = count
            lecture.transcription_language = language
            lecture.summary_status = Lecture.ProcessingStatus.READY
            lecture.summary_error = ""
            lecture.summary_generated_at = timezone.now()
            lecture.save(update_fields=[
                "transcript", "summary", "summary_word_count", "transcription_language",
                "summary_status", "summary_error", "summary_generated_at", "updated_at",
            ])
            return Response(self.get_serializer(lecture).data)
        except Exception as exc:
            logger.exception("Free-tier lecture summarization failed for lecture %s", lecture.id)
            lecture.summary_status = Lecture.ProcessingStatus.FAILED
            lecture.summary_error = str(exc)[:2000]
            lecture.save(update_fields=["summary_status", "summary_error", "updated_at"])
            return Response({"detail": lecture.summary_error}, status=502)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsFaculty, IsLectureParticipant],
    )
    def regenerate_summary(self, request, pk=None):
        if settings.FREE_TIER_MODE:
            return self.generate_summary(request, pk=pk)
        lecture = self.get_object()
        if lecture.summary_status == Lecture.ProcessingStatus.PROCESSING:
            return Response({"detail": "A summary is already being generated."}, status=409)
        lecture.summary_status = Lecture.ProcessingStatus.WAITING
        lecture.summary_error = ""
        lecture.save(update_fields=["summary_status", "summary_error", "updated_at"])

        def enqueue_after_commit():
            from .tasks import generate_lecture_summary
            try:
                generate_lecture_summary.delay(lecture.id)
            except Exception as exc:
                Lecture.objects.filter(pk=lecture.id).update(
                    summary_status=Lecture.ProcessingStatus.FAILED,
                    summary_error=f"Background queue is unavailable: {exc}"[:2000],
                )
                logger.exception("Could not queue summary retry for lecture %s", lecture.id)

        transaction.on_commit(enqueue_after_commit)
        return Response({"detail": "Summary generation has been queued."}, status=202)


class LiveClassViewSet(viewsets.ModelViewSet):
    serializer_class = LiveClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = LiveClass.objects.select_related("subject", "faculty")
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        if self.request.user.is_staff:
            return qs
        if profile.role == Profile.Role.FACULTY:
            return qs.filter(faculty=self.request.user)
        return qs.filter(subject__enrollments__student=self.request.user).distinct()

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated(), IsFaculty()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        subject = serializer.validated_data["subject"]
        if subject.faculty_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only schedule a live class for your own subject.")
        live_class = serializer.save(faculty=self.request.user)
        students = User.objects.filter(enrollments__subject=subject).distinct()
        notifications = [Notification(
            user=student,
            title="New live class scheduled",
            message=f"{live_class.title} for {subject.name} is scheduled for {timezone.localtime(live_class.starts_at):%d %b %Y, %I:%M %p}.",
            link=f"/live-classes/{live_class.id}",
        ) for student in students]
        Notification.objects.bulk_create(notifications)

    def perform_update(self, serializer):
        subject = serializer.validated_data.get("subject", serializer.instance.subject)
        if subject.faculty_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only schedule a live class for your own subject.")
        serializer.save()


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": True})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"updated": True})


class DashboardView(APIView):
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if profile.role == Profile.Role.FACULTY:
            subjects = Subject.objects.filter(faculty=request.user)
            lectures = Lecture.objects.filter(faculty=request.user)
            live_classes = LiveClass.objects.filter(faculty=request.user, starts_at__gte=timezone.now())
        else:
            subjects = Subject.objects.filter(enrollments__student=request.user)
            lectures = Lecture.objects.filter(subject__enrollments__student=request.user).distinct()
            live_classes = LiveClass.objects.filter(subject__enrollments__student=request.user, starts_at__gte=timezone.now()).distinct()
        return Response({
            "role": profile.role,
            "subjects": subjects.count(),
            "lectures": lectures.count(),
            "summaries_ready": lectures.filter(summary_status=Lecture.ProcessingStatus.READY).count(),
            "upcoming_live_classes": live_classes.count(),
            "unread_notifications": Notification.objects.filter(user=request.user, is_read=False).count(),
        })
