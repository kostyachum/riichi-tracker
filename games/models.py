# models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Player(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name


class Game(models.Model):
    played_at = models.DateTimeField(auto_now_add=True)
    oka_value = models.IntegerField(default=20000)   # total oka bonus (points)
    start_score = models.IntegerField(default=25000)
    target_score = models.IntegerField(default=30000)
    uma_top = models.IntegerField(default=20)
    uma_second = models.IntegerField(default=10)
    uma_third = models.IntegerField(default=-10)
    uma_last = models.IntegerField(default=-20)

    def __str__(self):
        return f"Game {self.id} on {self.played_at:%Y-%m-%d}"

    def calculate_final_scores(self):
        """Compute and store each player's adjusted score (with oka + uma)."""
        results = list(self.gameresult_set.all())
        if len(results) != 4 or any(r.rank for r in results):
            return
        results.sort(key=lambda r: r.score_raw, reverse=True)

        uma_values = [self.uma_top, self.uma_second,
                      self.uma_third, self.uma_last]

        for rank, (res, uma) in enumerate(zip(results, uma_values), start=1):
            diff_from_target = (res.score_raw - self.target_score) / 1000
            if rank == 1:
                diff_from_target += self.oka_value / 1000
            res.rank = rank
            res.score_adjusted = diff_from_target + uma
            res.save(update_fields=["rank", "score_adjusted"])


class GameResult(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    score_raw = models.IntegerField()              # e.g. 47000
    score_adjusted = models.FloatField(null=True)  # e.g. 37.0
    rank = models.PositiveSmallIntegerField(null=True)

    class Meta:
        unique_together = ("game", "player")

    def __str__(self):
        return f"{self.player} – {self.score_raw} ({self.rank})"


@receiver(post_save, sender=GameResult)
def recalc_after_save(sender, instance, **kwargs):
    instance.game.calculate_final_scores()
