from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin Interface
    path("admin/", admin.site.urls),
    # FAQ App URLs
    path("", include("faqs.urls")),
    # Authentication URLs
    path("auth/", include("authentication.urls")),
    # CKEditor Integration
    path("ckeditor5/", include("django_ckeditor_5.urls")),
]
