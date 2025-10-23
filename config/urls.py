from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from games.views import home


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]
