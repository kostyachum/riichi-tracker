from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet


class GameResultInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        total_raw = 0

        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue  # skip deleted/empty forms

            score_raw = form.cleaned_data.get("score_raw")

            if score_raw is not None:
                total_raw += score_raw

        if total_raw != 100000:
            raise ValidationError(f"Total raw score must equal 100,000 (got {total_raw}).")
