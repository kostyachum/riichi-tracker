import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# Serve user-uploaded media via Gunicorn for small deployments.
# For higher traffic, use a proper web server or object storage.
try:
    from django.conf import settings
    from whitenoise import WhiteNoise

    if getattr(settings, "MEDIA_ROOT", None):
        media_prefix = (getattr(settings, "MEDIA_URL", "/media/") or "/media/").lstrip("/")
        # Wrap the WSGI app with WhiteNoise and add MEDIA_ROOT with no caching
        application = WhiteNoise(application)
        application.add_files(str(settings.MEDIA_ROOT), prefix=media_prefix, max_age=0)
except Exception:
    # If WhiteNoise isn't available or settings not ready, skip media serving.
    # Django will still run; media should be served by the front-end proxy.
    pass
