from rest_framework import serializers

from .models import FAQ


class FAQSerializer(serializers.ModelSerializer):
    translated_question = serializers.SerializerMethodField()
    translated_answer = serializers.SerializerMethodField()

    class Meta:
        model = FAQ
        fields = [
            "id",
            "question",
            "answer",
            "translated_question",
            "translated_answer",
            "created_at",
            "updated_at",
        ]

    def get_translated_question(self, obj):
        lang = self.context.get("lang", "en")
        return obj.get_translated_content(lang)["question"]

    def get_translated_answer(self, obj):
        lang = self.context.get("lang", "en")
        return obj.get_translated_content(lang)["answer"]
