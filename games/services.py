from django.db.models import Prefetch, Avg, Count, Q
from .models import Game, GameResult, Player, Club


def get_latest_games(club_id=None, game_ids=None):
    results_qs = GameResult.objects.select_related("player").order_by("rank", "-score_raw")

    games_qs = Game.objects.all()

    if game_ids:
        games_qs = games_qs.filter(id__in=game_ids)

    if club_id:
        games_qs = games_qs.filter(
            gameresult__player__clubs__id=club_id
        ).distinct()

    return games_qs.order_by("-played_at").prefetch_related(Prefetch("gameresult_set", queryset=results_qs))[:50]


def get_club_id_by_slug(club_slug):
    ids = Club.objects.filter(slug=club_slug).values_list("id", flat=True)
    return ids[0] if ids else None


def get_all_clubs():
    return Club.objects.all().order_by("name")
