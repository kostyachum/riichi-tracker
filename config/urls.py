from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from games.views import home, player_profile, create_game_highlight


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path('i18n/', include('django.conf.urls.i18n')),
    path("player/<int:player_id>/", player_profile, name="player_profile"),
    path("highlights/create/", create_game_highlight, name="game_highlight_create"),
]

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
