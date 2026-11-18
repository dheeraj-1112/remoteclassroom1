from rest_framework.permissions import BasePermission


class IsFaculty(BasePermission):
    message = "Only a faculty account can perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        from .models import Profile
        profile = Profile.objects.filter(user=request.user).first()
        return bool(profile and profile.role == Profile.Role.FACULTY)


class IsLectureParticipant(BasePermission):
    """Faculty who owns the subject or students enrolled in its subject may access a lecture."""
    message = "You must teach or be enrolled in this lecture's subject."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if obj.faculty_id == user.id:
            return True
        if user.is_staff:
            return True
        return obj.subject.enrollments.filter(student=user).exists()


class IsSubjectFacultyOwner(BasePermission):
    message = "You can only modify subjects assigned to your faculty account."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or obj.faculty_id == request.user.id)
