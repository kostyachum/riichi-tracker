from django.utils import timezone

from .models import Birthday


def get_today_birthdays(today=None):
    today = today or timezone.localdate()
    return Birthday.objects.filter(
        is_active=True,
        month=today.month,
        day=today.day,
    ).order_by("sort_order", "friend_name")
