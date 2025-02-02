from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import FAQ


class FAQForm(forms.ModelForm):
    """
    Form for FAQ creation and editing with CKEditor5 support
    """

    question = forms.CharField(
        widget=CKEditor5Widget(config_name="extends"), required=True
    )
    answer = forms.CharField(
        widget=CKEditor5Widget(config_name="extends"), required=True
    )

    class Meta:
        model = FAQ
        fields = ["question", "answer"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
