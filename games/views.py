from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q
from .models import GameResult, Player
from .services import get_latest_games, get_all_clubs, get_club_id_by_slug


def home(request):
    club_slug = request.GET.get("club")
    club_id = get_club_id_by_slug(club_slug) if club_slug else None
    games = get_latest_games(club_id=club_id)
    clubs = get_all_clubs()
    data = {"games": games, "clubs": clubs,}
    return render(request, "home.html", data)


def player_profile(request, player_id):
    player = get_object_or_404(Player.objects.select_related('avatar').prefetch_related('clubs'), pk=player_id)
    results = GameResult.objects.filter(player=player)
    game_ids = list(results.values_list("game_id", flat=True))
    games = get_latest_games(game_ids=game_ids) if game_ids else []
    stats = results.aggregate(
        avg_score=Avg("score_adjusted"),
        avg_raw=Avg("score_raw"),
        avg_rank=Avg("rank"),
        total_games=Count("id"),
        wins=Count("id", filter=Q(rank=1)),
    )
    stats["win_rate"] = (stats["wins"] / stats["total_games"] * 100) if stats["total_games"] else 0
    recent_results = (
        results
        .order_by("-created_at")[:10]
        .values_list("rank", flat=True)
    )
    recent_ranks = list(reversed(recent_results))
    return render(request, "games/player_profile.html", {
        "player": player,
        "games": games,
        "stats": stats,
        "recent_ranks": recent_ranks,
    })
