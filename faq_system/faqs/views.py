from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .forms import FAQForm
from .models import FAQ
from .serializers import FAQSerializer


def get_cache_key(prefix, identifier=None, lang="en"):
    """Generate cache key for FAQ-related data."""
    if identifier:
        return f"faq:{prefix}:{identifier}:{lang}"
    return f"faq:{prefix}:{lang}"


def clear_faq_cache(func):
    """Decorator to clear all FAQ-related caches after data modifications."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        cache_keys = cache.keys("faq:*")
        if cache_keys:
            cache.delete_many(cache_keys)
        return result

    return wrapper


class FAQViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FAQ CRUD operations with caching and translation support.
    Provides endpoints for managing FAQs with language-specific content.
    """

    queryset = FAQ.objects.all().order_by("-created_at")
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        """Add language preference to serializer context."""
        context = super().get_serializer_context()
        context["lang"] = self.request.query_params.get("lang", "en")
        return context

    def list(self, request, *args, **kwargs):
        """List FAQs with caching support for each language."""
        lang = request.query_params.get("lang", "en")
        cache_key = get_cache_key("list", lang=lang)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        timeout = getattr(settings, "FAQ_SETTINGS", {}).get("CACHE_TIMEOUT", 60 * 60)
        cache.set(cache_key, data, timeout=timeout)
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single FAQ with language-specific caching."""
        lang = request.query_params.get("lang", "en")
        instance = self.get_object()
        cache_key = get_cache_key("detail", instance.pk, lang)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        serializer = self.get_serializer(instance)
        data = serializer.data

        timeout = getattr(settings, "FAQ_SETTINGS", {}).get("CACHE_TIMEOUT", 60 * 60)
        cache.set(cache_key, data, timeout=timeout)
        return Response(data)

    @clear_faq_cache
    def create(self, request, *args, **kwargs):
        """Create FAQ with automatic cache clearing."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @clear_faq_cache
    def update(self, request, *args, **kwargs):
        """Update FAQ with automatic cache clearing."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            with transaction.atomic():
                self.perform_update(serializer)
                return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @clear_faq_cache
    def destroy(self, request, *args, **kwargs):
        """Delete FAQ with automatic cache clearing."""
        instance = self.get_object()
        with transaction.atomic():
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @clear_faq_cache
    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Create multiple FAQs in a single request."""
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            with transaction.atomic():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_faqs_with_translations(lang):
    """
    Retrieve all FAQs with translations for specified language.
    Uses caching to improve performance.
    """
    cache_key = f"faq:list_data:{lang}"
    cached_data = cache.get(cache_key)

    if cached_data is None:
        faqs = FAQ.objects.all().order_by("-created_at")
        translated_faqs = [
            {"id": faq.id, **faq.get_translated_content(lang)} for faq in faqs
        ]

        timeout = getattr(settings, "FAQ_SETTINGS", {}).get(
            "CACHE_TIMEOUT", 60 * 60 * 24
        )
        cache.set(cache_key, translated_faqs, timeout=timeout)
        return translated_faqs

    return cached_data


def faq_list(request):
    """Display list of FAQs with language selection support."""
    lang = request.GET.get("lang", "en")
    translated_faqs = get_faqs_with_translations(lang)

    context = {
        "faqs": translated_faqs,
        "current_lang": lang,
        "available_languages": [("en", "English"), ("hi", "Hindi"), ("bn", "Bengali")],
    }
    return render(request, "faqs/faq_list.html", context)


@login_required
def faq_create(request):
    """Create new FAQ with cache management."""
    if request.method == "POST":
        form = FAQForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()

                languages = getattr(settings, "FAQ_SETTINGS", {}).get(
                    "LANGUAGES", ["en", "hi", "bn"]
                )
                cache_keys = []

                for lang in languages:
                    cache_keys.extend(
                        [
                            get_cache_key("list", lang=lang),
                            get_cache_key("list_data", lang=lang),
                        ]
                    )

                if cache_keys:
                    cache.delete_many(cache_keys)

                messages.success(request, "FAQ created successfully!")
                return redirect("faq_list")
    else:
        form = FAQForm()

    return render(request, "faqs/faq_form.html", {"form": form, "title": "Create FAQ"})


@login_required
def faq_edit(request, pk):
    """Edit FAQ with translation preview and cache management."""
    faq = get_object_or_404(FAQ, pk=pk)

    if request.method == "POST":
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            with transaction.atomic():
                faq = form.save(commit=False)
                faq.save()
                form.save_m2m()

                languages = getattr(settings, "FAQ_SETTINGS", {}).get(
                    "LANGUAGES", ["en", "hi", "bn"]
                )
                cache_keys = []

                for lang in languages:
                    cache_keys.extend(
                        [
                            get_cache_key("list", lang=lang),
                            get_cache_key("list_data", lang=lang),
                            get_cache_key("detail", faq.pk, lang),
                        ]
                    )

                if cache_keys:
                    cache.delete_many(cache_keys)

                messages.success(request, "FAQ updated successfully!")
                return redirect("faq_list")
    else:
        form = FAQForm(instance=faq)

    translations = {}
    languages = getattr(settings, "FAQ_SETTINGS", {}).get(
        "LANGUAGES", ["en", "hi", "bn"]
    )
    for lang in languages:
        if lang != "en":
            translations[lang] = faq.get_translated_content(lang)

    return render(
        request,
        "faqs/faq_form.html",
        {
            "form": form,
            "title": "Edit FAQ",
            "faq": faq,
            "translations": translations,
            "available_languages": [
                ("en", "English"),
                ("hi", "Hindi"),
                ("bn", "Bengali"),
            ],
        },
    )


@login_required
def faq_delete(request, pk):
    """Delete FAQ with translation preview and cache clearing."""
    faq = get_object_or_404(FAQ, pk=pk)

    if request.method == "POST":
        with transaction.atomic():
            languages = getattr(settings, "FAQ_SETTINGS", {}).get(
                "LANGUAGES", ["en", "hi", "bn"]
            )
            cache_keys = []

            for lang in languages:
                cache_keys.extend(
                    [
                        get_cache_key("list", lang=lang),
                        get_cache_key("list_data", lang=lang),
                        get_cache_key("detail", faq.pk, lang),
                    ]
                )

            if cache_keys:
                cache.delete_many(cache_keys)

            faq.delete()

            messages.success(request, "FAQ deleted successfully!")
            return redirect("faq_list")

    translations = {}
    languages = getattr(settings, "FAQ_SETTINGS", {}).get(
        "LANGUAGES", ["en", "hi", "bn"]
    )
    for lang in languages:
        if lang != "en":
            translations[lang] = faq.get_translated_content(lang)

    return render(
        request,
        "faqs/faq_confirm_delete.html",
        {
            "faq": faq,
            "translations": translations,
            "available_languages": [
                ("en", "English"),
                ("hi", "Hindi"),
                ("bn", "Bengali"),
            ],
        },
    )
