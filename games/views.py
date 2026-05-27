from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.contrib.auth.decorators import login_required
from urllib.parse import urlparse, parse_qs
from birthdays.services import get_today_birthdays
from .models import GameResult, Player, Game, GameHighlight
from .services import get_latest_games, get_all_clubs, get_club_id_by_slug
from .forms import GameCreateForm


def _get_club_slug(request):
    club_slug = request.GET.get("club")
    if club_slug:
        return club_slug

    next_url = request.POST.get("next")
    if not next_url:
        return None

    query = parse_qs(urlparse(next_url).query)
    return query.get("club", [None])[0]


def _render_home(request, game_form=None, show_game_modal=False):
    club_slug = _get_club_slug(request)
    club_id = get_club_id_by_slug(club_slug) if club_slug else None
    games = get_latest_games(club_id=club_id)
    clubs = get_all_clubs()
    data = {
        "games": games,
        "clubs": clubs,
        "birthdays": get_today_birthdays(),
        "game_form": game_form or GameCreateForm(),
        "show_game_modal": show_game_modal,
    }
    return render(request, "home.html", data)


def home(request):
    return _render_home(request)


def player_profile(request, player_id):
    player = get_object_or_404(Player.objects.select_related('avatar').prefetch_related('clubs'), pk=player_id)
    results = GameResult.objects.filter(player=player)
    ranked_results = results.exclude(game__is_unranked=True)
    game_ids = list(results.values_list("game_id", flat=True))
    games = get_latest_games(game_ids=game_ids) if game_ids else []
    stats = ranked_results.aggregate(
        avg_score=Avg("score_adjusted"),
        avg_raw=Avg("score_raw"),
        avg_rank=Avg("rank"),
        total_games=Count("id"),
        wins=Count("id", filter=Q(rank=1)),
    )
    stats["win_rate"] = (stats["wins"] / stats["total_games"] * 100) if stats["total_games"] else 0
    recent_results = (
        ranked_results
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


def create_game_highlight(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    game_id = request.POST.get("game_id")
    player_id = request.POST.get("player_id") or None
    caption = request.POST.get("caption", "").strip()
    photos = request.FILES.getlist("photos")

    if not photos:
        return HttpResponseBadRequest("No photos uploaded")

    game = get_object_or_404(Game, pk=game_id) if game_id else None
    player = get_object_or_404(Player, pk=player_id) if player_id else None

    if game and player and not GameResult.objects.filter(game=game, player=player).exists():
        return HttpResponseBadRequest("Player not in game")

    for photo in photos:
        GameHighlight.objects.create(
            game=game,
            player=player,
            photo=photo,
            caption=caption,
        )

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required(login_url="/admin/login/")
def create_game(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    form = GameCreateForm(request.POST)
    if not form.is_valid():
        return _render_home(request, game_form=form, show_game_modal=True)

    with transaction.atomic():
        game = Game.objects.create(is_unranked=form.cleaned_data["is_unranked"])
        for result in form.cleaned_results():
            GameResult.objects.create(game=game, **result)

    return redirect("/")
