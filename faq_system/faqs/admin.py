from django.contrib import admin
from django.core.cache import cache
from django.utils.html import format_html, strip_tags
from django.utils.translation import gettext_lazy as _

from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin configuration for FAQ model."""

    list_display = ("truncated_question", "created_at", "updated_at", "preview_answer")
    list_filter = ("created_at", "updated_at")
    search_fields = ("question", "answer")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("question", "answer")}),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def truncated_question(self, obj):
        """Truncate long questions for display"""
        return obj.question[:100] + "..." if len(obj.question) > 100 else obj.question

    truncated_question.short_description = _("Question")

    def preview_answer(self, obj):
        """Generate HTML preview of answer"""
        if not obj.answer:
            return ""

        plain_text = strip_tags(obj.answer)
        plain_text = (
            str(plain_text)
            .replace(" ", " ")
            .replace("&", "&")
            .replace(">", ">")
            .replace("<", "<")
        )
        preview_text = plain_text[:150] + ("..." if len(plain_text) > 150 else "")

        return format_html("{}", preview_text)

    preview_answer.short_description = _("Answer Preview")

    class Media:
        css = {
            "all": (
                "admin/css/ckeditor-custom.css",
                "admin/css/custom_faq.css",
            )
        }
        js = ("admin/js/custom_faq.js",)

    def get_queryset(self, request):
        """Optimize query performance"""
        return super().get_queryset(request).select_related()

    def save_model(self, request, obj, form, change):
        """Clear cache on save"""
        super().save_model(request, obj, form, change)
        supported_langs = ["en", "hi", "bn"]
        for lang in supported_langs:
            cache_key = obj._get_cache_key("content", lang)
            cache.delete(cache_key)
