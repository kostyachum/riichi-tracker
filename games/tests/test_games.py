import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from django.urls import reverse
from django.utils import timezone
from games.models import Game, GameResult, Player, Club
from games.forms import GameResultInlineFormSet
from games.services import get_latest_games


def make_game(played_at, players, scores):
    """Helper: create a 4-player game with given players & scores."""
    game = Game.objects.create(played_at=played_at)
    ranked = sorted(zip(players, scores), key=lambda x: x[1], reverse=True)
    for rank, (player, score) in enumerate(ranked, start=1):
        GameResult.objects.create(
            game=game,
            player=player,
            score_raw=score,
            rank=rank,
        )
    return game


@pytest.mark.django_db
def test_get_latest_games_filters_by_club():
    # Create two clubs
    club_a = Club.objects.create(name="Tokyo Riichi", slug="tokyo")
    club_b = Club.objects.create(name="Osaka South", slug="osaka")

    # Create players and assign to clubs
    pa1, pa2 = Player.objects.create(name="A1"), Player.objects.create(name="A2")
    pb1, pb2 = Player.objects.create(name="B1"), Player.objects.create(name="B2")
    pa1.clubs.add(club_a)
    pa2.clubs.add(club_a)
    pb1.clubs.add(club_b)
    pb2.clubs.add(club_b)

    # Game1: mix of both clubs
    g1_players = [pa1, pb1, pa2, pb2]
    g1_scores = [40000, 32000, 18000, 10000]
    game1 = make_game(timezone.now() - timedelta(days=1), g1_players, g1_scores)

    # Game2: only club A
    g2_players = [pa1, pa2, Player.objects.create(name="Guest1"), Player.objects.create(name="Guest2")]
    g2_scores = [35000, 33000, 20000, 12000]
    game2 = make_game(timezone.now(), g2_players, g2_scores)

    # Game3: only club B
    g3_players = [pb1, pb2, Player.objects.create(name="Visitor1"), Player.objects.create(name="Visitor2")]
    g3_scores = [36000, 30000, 22000, 12000]
    game3 = make_game(timezone.now() - timedelta(days=2), g3_players, g3_scores)

    # club A should see games 1 & 2
    games_a = list(get_latest_games(club_id=club_a.id))
    ids_a = {g.id for g in games_a}
    assert ids_a == {game1.id, game2.id}

    # club B should see games 1 & 3
    games_b = list(get_latest_games(club_id=club_b.id))
    ids_b = {g.id for g in games_b}
    assert ids_b == {game1.id, game3.id}

    # nonexistent club → empty
    assert list(get_latest_games(club_id=9999)) == []


@pytest.mark.django_db
def test_get_latest_games_filters_by_ids_and_ordering():
    club = Club.objects.create(name="Shinjuku", slug="shinjuku")
    players = [Player.objects.create(name=f"P{i+1}") for i in range(4)]
    for p in players:
        p.clubs.add(club)

    g_old = make_game(timezone.now() - timedelta(days=5), players, [40000, 30000, 20000, 10000])
    g_new = make_game(timezone.now(), players, [35000, 33000, 20000, 12000])

    # Filter by explicit IDs
    games = list(get_latest_games(game_ids=[g_old.id]))
    assert [g.id for g in games] == [g_old.id]

    # Ordering check (latest first)
    all_games = list(get_latest_games())
    assert [g.id for g in all_games] == [g_new.id, g_old.id]


@pytest.mark.django_db
def test_create_game_creates_unranked_game_and_results(client):
    user = get_user_model().objects.create_user(username="editor", password="secret")
    client.force_login(user)
    players = [Player.objects.create(name=f"Player {index}") for index in range(1, 5)]

    response = client.post(
        reverse("game_create"),
        {
            "is_unranked": "on",
            "player_1": players[0].id,
            "score_1": 32000,
            "player_2": players[1].id,
            "score_2": 28000,
            "player_3": players[2].id,
            "score_3": 22000,
            "player_4": players[3].id,
            "score_4": 18000,
            "next": "/",
        },
    )

    assert response.status_code == 302
    game = Game.objects.get()
    assert game.is_unranked is True
    assert GameResult.objects.filter(game=game).count() == 4
    assert set(GameResult.objects.filter(game=game).values_list("score_raw", flat=True)) == {32000, 28000, 22000, 18000}


@pytest.mark.django_db
def test_create_game_rejects_duplicate_players(client):
    user = get_user_model().objects.create_user(username="editor", password="secret")
    client.force_login(user)
    players = [Player.objects.create(name=f"Player {index}") for index in range(1, 4)]

    response = client.post(
        reverse("game_create"),
        {
            "player_1": players[0].id,
            "score_1": 25000,
            "player_2": players[0].id,
            "score_2": 25000,
            "player_3": players[1].id,
            "score_3": 25000,
            "player_4": players[2].id,
            "score_4": 25000,
            "next": "/",
        },
    )

    assert response.status_code == 200
    assert Game.objects.count() == 0
    assert "Each player must be unique." in response.content.decode()


@pytest.mark.django_db
def test_create_game_requires_login(client):
    response = client.post(reverse("game_create"), {"next": "/"})

    assert response.status_code == 302
    assert response["Location"].startswith("/admin/login/")


@pytest.mark.django_db
def test_game_result_inline_formset_allows_swapping_players():
    players = [Player.objects.create(name=f"Player {index}") for index in range(1, 5)]
    game = Game.objects.create()
    results = [
        GameResult.objects.create(game=game, player=players[0], score_raw=35000),
        GameResult.objects.create(game=game, player=players[1], score_raw=25000),
        GameResult.objects.create(game=game, player=players[2], score_raw=22000),
        GameResult.objects.create(game=game, player=players[3], score_raw=18000),
    ]

    formset_class = inlineformset_factory(
        Game,
        GameResult,
        formset=GameResultInlineFormSet,
        fields=("player", "score_raw"),
        extra=0,
        can_delete=True,
    )

    formset = formset_class(
        data={
            "gameresult_set-TOTAL_FORMS": "4",
            "gameresult_set-INITIAL_FORMS": "4",
            "gameresult_set-MIN_NUM_FORMS": "0",
            "gameresult_set-MAX_NUM_FORMS": "4",
            "gameresult_set-0-id": str(results[0].id),
            "gameresult_set-0-player": str(players[1].id),
            "gameresult_set-0-score_raw": "25000",
            "gameresult_set-1-id": str(results[1].id),
            "gameresult_set-1-player": str(players[0].id),
            "gameresult_set-1-score_raw": "35000",
            "gameresult_set-2-id": str(results[2].id),
            "gameresult_set-2-player": str(players[2].id),
            "gameresult_set-2-score_raw": "22000",
            "gameresult_set-3-id": str(results[3].id),
            "gameresult_set-3-player": str(players[3].id),
            "gameresult_set-3-score_raw": "18000",
        },
        instance=game,
    )

    assert formset.is_valid(), formset.errors
    formset.save()

    saved_pairs = list(
        GameResult.objects.filter(game=game).order_by("-score_raw").values_list("player_id", "score_raw")
    )
    assert saved_pairs == [
        (players[0].id, 35000),
        (players[1].id, 25000),
        (players[2].id, 22000),
        (players[3].id, 18000),
    ]
