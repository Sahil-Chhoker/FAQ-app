from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"faqs", views.FAQViewSet, basename="faq")

urlpatterns = [
    # Web Interface URLs
    path("", views.faq_list, name="faq_list"),
    path("faqs/", RedirectView.as_view(url="/", permanent=True)),
    path("create/", views.faq_create, name="faq_create"),
    path("<int:pk>/edit/", views.faq_edit, name="faq_edit"),
    path("<int:pk>/delete/", views.faq_delete, name="faq_delete"),
    # API URLs
    path("api/", include(router.urls)),
]
