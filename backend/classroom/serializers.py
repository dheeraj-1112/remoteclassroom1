from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from .models import Enrollment, Lecture, LiveClass, Notification, Profile, Subject

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "full_name", "role"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Profile.objects.update_or_create(user=user, defaults={"role": Profile.Role.STUDENT})
        return user


class SubjectSerializer(serializers.ModelSerializer):
    faculty_name = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    lecture_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subject
        fields = ["id", "name", "code", "description", "faculty", "faculty_name", "is_enrolled", "lecture_count", "created_at"]
        read_only_fields = ["faculty", "created_at"]

    def get_faculty_name(self, obj):
        return obj.faculty.get_full_name() or obj.faculty.username

    def get_is_enrolled(self, obj):
        user = self.context["request"].user
        return obj.enrollments.filter(student=user).exists()


class EnrollmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "subject", "subject_name", "subject_code", "enrolled_at"]
        read_only_fields = ["enrolled_at"]


class LectureSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    faculty_name = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    hls_url = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = [
            "id", "subject", "subject_name", "subject_code", "faculty", "faculty_name",
            "title", "topic", "description", "video", "video_url", "duration_seconds",
            "hls_url", "hls_status", "transcript", "summary", "summary_word_count",
            "summary_status", "summary_error", "transcription_language", "summary_generated_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "faculty", "hls_master_key", "hls_status", "transcript", "summary", "summary_word_count",
            "summary_status", "summary_error", "transcription_language", "summary_generated_at", "created_at", "updated_at",
        ]

    def get_faculty_name(self, obj):
        return obj.faculty.get_full_name() or obj.faculty.username

    def get_video_url(self, obj):
        try:
            return obj.video.url
        except (ValueError, AttributeError):
            return ""

    def get_hls_url(self, obj):
        if not obj.hls_master_key:
            return ""
        from django.core.files.storage import default_storage
        return default_storage.url(obj.hls_master_key)

    def validate_video(self, value):
        if not value:
            raise serializers.ValidationError("A lecture video is required.")
        max_mb = 1024
        try:
            from django.conf import settings
            max_mb = settings.MAX_LECTURE_UPLOAD_MB
        except Exception:
            pass
        if value.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError(f"The video exceeds the {max_mb} MB upload limit.")
        from django.conf import settings
        if settings.FREE_TIER_MODE:
            if value.size > 25 * 1024 * 1024:
                raise serializers.ValidationError("Free cloud transcription supports videos up to 25 MB. Compress the video before uploading.")
            if value.name.rsplit(".", 1)[-1].lower() not in {"mp4", "webm"}:
                raise serializers.ValidationError("For free cloud processing, upload an MP4 or WEBM video.")
        else:
            allowed = {"video/mp4", "video/quicktime", "video/x-matroska", "video/webm", "video/x-msvideo", "application/octet-stream"}
            if getattr(value, "content_type", None) and value.content_type not in allowed:
                raise serializers.ValidationError("Upload an MP4, MOV, MKV, WEBM or AVI video.")
        return value


class LiveClassSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    faculty_name = serializers.SerializerMethodField()

    class Meta:
        model = LiveClass
        fields = ["id", "subject", "subject_name", "subject_code", "faculty", "faculty_name", "title", "description", "starts_at", "meeting_url", "created_at"]
        read_only_fields = ["faculty", "created_at"]

    def get_faculty_name(self, obj):
        return obj.faculty.get_full_name() or obj.faculty.username

    def validate_starts_at(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Choose a future date and time for the live class.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "link", "is_read", "created_at"]
        read_only_fields = ["title", "message", "link", "created_at"]
