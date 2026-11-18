from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from classroom.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health"),
    path("api/", include("classroom.urls")),
]

if settings.DEBUG and not getattr(settings, "AWS_STORAGE_BUCKET_NAME", None):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
