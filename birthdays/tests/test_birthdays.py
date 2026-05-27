from datetime import date

import pytest
from django.core.exceptions import ValidationError

from birthdays.models import Birthday
from birthdays.services import get_today_birthdays


@pytest.mark.django_db
def test_get_today_birthdays_returns_active_matches_in_display_order():
    Birthday.objects.create(friend_name="Later", month=5, day=27, sort_order=20)
    Birthday.objects.create(friend_name="Earlier", month=5, day=27, sort_order=10)
    Birthday.objects.create(friend_name="Inactive", month=5, day=27, is_active=False)
    Birthday.objects.create(friend_name="Other Day", month=5, day=28)

    birthdays = list(get_today_birthdays(date(2026, 5, 27)))

    assert [birthday.friend_name for birthday in birthdays] == ["Earlier", "Later"]


def test_birthday_rejects_invalid_calendar_day():
    birthday = Birthday(friend_name="Invalid", month=2, day=31)

    with pytest.raises(ValidationError):
        birthday.full_clean()
