from django.shortcuts import render
from django.db.models import Prefetch
from .models import Game, GameResult


def home(request):
    results_qs = GameResult.objects.select_related("player").order_by("rank", "-score_raw")
    games = (
        Game.objects.order_by("-played_at")
        .prefetch_related(Prefetch("gameresult_set", queryset=results_qs))[:50]
    )
    return render(request, "home.html", {"games": games})
