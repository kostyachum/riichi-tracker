from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import GameResult, Player


EXPECTED_TOTAL_RAW_SCORE = 100000


def raw_score_total_error(total_score):
    delta = EXPECTED_TOTAL_RAW_SCORE - total_score
    if delta > 0:
        delta_text = f"missing {delta:,} points"
    else:
        delta_text = f"exceeds by {abs(delta):,} points"
    return ValidationError(
        f"Total raw score must equal {EXPECTED_TOTAL_RAW_SCORE:,} ({delta_text}; got {total_score:,})."
    )


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

        if total_raw != EXPECTED_TOTAL_RAW_SCORE:
            raise raw_score_total_error(total_raw)

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        results_data = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            player = form.cleaned_data.get("player")
            score_raw = form.cleaned_data.get("score_raw")
            if player is None or score_raw is None:
                continue

            results_data.append(
                {
                    "player": player,
                    "score_raw": score_raw,
                }
            )

        with transaction.atomic():
            GameResult.objects.filter(game=self.instance).delete()
            saved_results = [
                GameResult.objects.create(game=self.instance, **result_data)
                for result_data in results_data
            ]

        self.deleted_objects = []
        self.changed_objects = []
        self.new_objects = saved_results
        return saved_results


class GameCreateForm(forms.Form):
    is_unranked = forms.BooleanField(required=False)
    player_1 = forms.ModelChoiceField(queryset=Player.objects.none(), empty_label="Select player")
    score_1 = forms.IntegerField()
    player_2 = forms.ModelChoiceField(queryset=Player.objects.none(), empty_label="Select player")
    score_2 = forms.IntegerField()
    player_3 = forms.ModelChoiceField(queryset=Player.objects.none(), empty_label="Select player")
    score_3 = forms.IntegerField()
    player_4 = forms.ModelChoiceField(queryset=Player.objects.none(), empty_label="Select player")
    score_4 = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        player_qs = Player.objects.order_by("name")
        for index in range(1, 5):
            self.fields[f"player_{index}"].queryset = player_qs
            self.fields[f"player_{index}"].widget.attrs.update({"class": "select select-bordered w-full"})
            self.fields[f"score_{index}"].widget.attrs.update({"class": "input input-bordered w-full", "placeholder": "25000"})
        self.fields["is_unranked"].widget.attrs.update({"class": "checkbox checkbox-sm"})

    def clean(self):
        cleaned_data = super().clean()

        players = []
        scores = []
        for index in range(1, 5):
            player = cleaned_data.get(f"player_{index}")
            score = cleaned_data.get(f"score_{index}")
            if player is not None:
                players.append(player)
            if score is not None:
                scores.append(score)

        if len(players) != 4 or len(scores) != 4:
            return cleaned_data

        unique_player_ids = {player.id for player in players}
        if len(unique_player_ids) != 4:
            raise ValidationError("Each player must be unique.")

        total_score = sum(scores)
        if total_score != EXPECTED_TOTAL_RAW_SCORE:
            raise raw_score_total_error(total_score)

        return cleaned_data

    def cleaned_results(self):
        return [
            {
                "player": self.cleaned_data[f"player_{index}"],
                "score_raw": self.cleaned_data[f"score_{index}"],
            }
            for index in range(1, 5)
        ]


class GameResultInlineForm(forms.ModelForm):
    class Meta:
        model = GameResult
        fields = "__all__"

    def validate_unique(self):
        # Admin swaps can temporarily look like duplicate (game, player) pairs
        # against rows that are about to be replaced atomically by the formset.
        return
