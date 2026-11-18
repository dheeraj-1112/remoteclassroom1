from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardView, LectureViewSet, LiveClassViewSet, LoginView, LogoutView,
    MeView, NotificationViewSet, RegisterView, SubjectViewSet,
)

router = DefaultRouter()
router.register("subjects", SubjectViewSet, basename="subject")
router.register("lectures", LectureViewSet, basename="lecture")
router.register("live-classes", LiveClassViewSet, basename="live-class")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include(router.urls)),
]
