from calendar import monthrange

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext as _


class Birthday(models.Model):
    friend_name = models.CharField(max_length=100)
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    day = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    celebratory_image = models.FileField(upload_to="birthdays/", blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("month", "day", "sort_order", "friend_name")

    def __str__(self):
        return f"{self.friend_name} ({self.month:02d}-{self.day:02d})"

    def clean(self):
        super().clean()
        if self.month and self.day and self.day > monthrange(2000, self.month)[1]:
            raise ValidationError({"day": _("Enter a valid day for this month.")})
