from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from games.views import home, player_profile


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("player/<int:player_id>/", player_profile, name="player_profile"),
]

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
