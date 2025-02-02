from django.db import migrations, models
import django_ckeditor_5.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FAQ",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "question",
                    django_ckeditor_5.fields.CKEditor5Field(verbose_name="Question"),
                ),
                (
                    "answer",
                    django_ckeditor_5.fields.CKEditor5Field(verbose_name="Answer"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "FAQ",
                "verbose_name_plural": "FAQs",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["created_at"], name="faqs_faq_created_f6584d_idx"
                    ),
                    models.Index(
                        fields=["question"], name="faqs_faq_questio_2ed515_idx"
                    ),
                ],
            },
        ),
    ]
