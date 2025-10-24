from django.contrib import admin
from .models import Player, Game, GameResult
from .forms import GameResultInlineFormSet


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


class GameResultInline(admin.TabularInline):
    model = GameResult
    formset = GameResultInlineFormSet
    extra = 4
    min_num = 0
    max_num = 4
    autocomplete_fields = ("player",)
    fields = ("player", "score_raw", "score_adjusted", "rank")
    readonly_fields = ("score_adjusted", "rank")


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "played_at",
        "start_score",
        "target_score",
        "oka_value",
    )
    list_filter = ("played_at",)
    date_hierarchy = "played_at"
    inlines = [GameResultInline]
    readonly_fields = ()

    actions = [
        "recalculate_scores",
    ]

    @admin.action(description="Recalculate final scores")
    def recalculate_scores(self, request, queryset):
        for game in queryset:
            game.calculate_final_scores()


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "player", "score_raw", "score_adjusted", "rank")
    list_select_related = ("game", "player")
    list_filter = ("rank", "game", "player")
    search_fields = ("player__name",)
    ordering = ("-game__played_at", "rank")
    autocomplete_fields = ("player",)
    raw_id_fields = ("game",)
