import logging

from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from googletrans import Translator

from faq_system import settings

logger = logging.getLogger(__name__)


class FAQ(models.Model):
    """
    FAQ model for managing multilingual questions and answers.

    Uses CKEditor5 for rich text editing and provides automatic translation
    with caching support for multiple languages.
    """

    question = CKEditor5Field(_("Question"), config_name="extends")
    answer = CKEditor5Field(_("Answer"), config_name="extends")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _get_cache_key(self, field, lang):
        """Generate cache key for field translation."""
        return f"faq:translation:{self.id}:{field}:{lang}"

    def _clear_translations_cache(self):
        """Clear all cached translations for this FAQ."""
        from django.conf import settings

        languages = getattr(settings, "FAQ_SETTINGS", {}).get(
            "LANGUAGES", ["en", "hi", "bn"]
        )
        # Generate cache keys for both question and answer in all languages
        cache_keys = [self._get_cache_key("question", lang) for lang in languages] + [
            self._get_cache_key("answer", lang) for lang in languages
        ]
        cache.delete_many(cache_keys)

    def _translate_text(self, text, lang):
        """
        Translate text to specified language with caching support.

        Returns original text if translation fails or language is English.
        """
        if lang == "en":
            return text

        cache_key = f"faq:translation:{hash(text)}:{lang}"
        cached_translation = cache.get(cache_key)

        if cached_translation is not None:
            return cached_translation

        try:
            translator = Translator()
            translation = translator.translate(text, dest=lang)
            translated_text = translation.text

            # Cache translation with configurable timeout
            timeout = getattr(settings, "FAQ_SETTINGS", {}).get(
                "TRANSLATION_CACHE_TIMEOUT", 60 * 60 * 24
            )
            cache.set(cache_key, translated_text, timeout=timeout)

            return translated_text
        except Exception as e:
            logger.error(f"Translation failed for language {lang}: {str(e)}")
            return text

    def get_translated_content(self, lang="en"):
        """
        Get FAQ content in specified language.

        Args:
            lang (str): Target language code (default: 'en')

        Returns:
            dict: Translated FAQ content with metadata
        """
        if lang == "en":
            return {
                "question": self.question,
                "answer": self.answer,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }

        cache_key = f"faq:content:{self.id}:{lang}"
        cached_content = cache.get(cache_key)

        if cached_content is not None:
            return cached_content

        # Translate and cache content
        translated_content = {
            "question": self._translate_text(self.question, lang),
            "answer": self._translate_text(self.answer, lang),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        timeout = getattr(settings, "FAQ_SETTINGS", {}).get("CACHE_TIMEOUT", 60 * 60)
        cache.set(cache_key, translated_content, timeout=timeout)
        return translated_content

    def save(self, *args, **kwargs):
        """Override save to clear translation cache."""
        self._clear_translations_cache()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to clear translation cache."""
        self._clear_translations_cache()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.question[:50]

    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["question"]),
        ]
