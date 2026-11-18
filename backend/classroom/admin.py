from django.contrib import admin
from .models import Enrollment, Lecture, LiveClass, Notification, Profile, Subject

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "faculty", "created_at")
    search_fields = ("code", "name", "faculty__username")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "enrolled_at")
    list_filter = ("subject",)

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "faculty", "hls_status", "summary_status", "created_at")
    list_filter = ("hls_status", "summary_status", "subject")
    search_fields = ("title", "topic", "subject__name")

@admin.register(LiveClass)
class LiveClassAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "faculty", "starts_at")
    list_filter = ("subject",)

admin.site.register(Notification)
