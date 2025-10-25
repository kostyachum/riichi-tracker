import pytest
from datetime import timedelta
from django.utils import timezone
from games.models import Game, GameResult, Player, Club
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
