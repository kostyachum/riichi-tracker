import zoneinfo

from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.readTimezoneCookie(request, activate=True)

        return self.get_response(request)

    def readTimezoneCookie(self, request, activate: bool = True):
        gmt_offset = (request.COOKIES.get("GMT_OFFSET") or '').strip()
        if gmt_offset.replace('-', '').isdigit():
            tz = timezone.get_fixed_timezone(int(gmt_offset))
            if activate:
                timezone.activate(tz)
            return tz
        return None