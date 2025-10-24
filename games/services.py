from django.db.models import Prefetch, Avg, Count, Q
from .models import Game, GameResult, Player


def get_latest_games(game_ids=None):
    results_qs = GameResult.objects.select_related("player").order_by("rank", "-score_raw")
    games = Game.objects.filter(id__in=game_ids) if game_ids else Game.objects.all()
    return games.order_by("-played_at").prefetch_related(Prefetch("gameresult_set", queryset=results_qs))[:50]
