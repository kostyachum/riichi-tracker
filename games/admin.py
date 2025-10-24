from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Player, Game, GameResult, Avatar
from .forms import GameResultInlineFormSet


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "avatar_img")
    search_fields = ("name",)
    ordering = ("name",)
    autocomplete_fields = ()
    raw_id_fields = ("avatar",)
    readonly_fields = ('avatar_img',)

    def avatar_img(self, instance):
        if instance.avatar:
            return mark_safe(f'<img src="{instance.avatar.file.url}" width="100" />')
        return '-'


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = ("file", "id", "uploaded_at")
    search_fields = ("file",)
    ordering = ("-uploaded_at",)


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

# Admin branding
admin.site.site_header = "Riichi Tracker Admin"
admin.site.site_title = "Riichi Tracker"
admin.site.index_title = "Dashboard"
