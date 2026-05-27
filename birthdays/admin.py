from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Birthday


@admin.register(Birthday)
class BirthdayAdmin(admin.ModelAdmin):
    list_display = ("friend_name", "month", "day", "is_active", "sort_order", "image_preview")
    list_filter = ("is_active", "month")
    search_fields = ("friend_name",)
    ordering = ("month", "day", "sort_order", "friend_name")
    readonly_fields = ("image_preview",)

    def image_preview(self, instance):
        if instance.celebratory_image:
            return mark_safe(f'<img src="{instance.celebratory_image.url}" width="120" />')
        return "-"

    image_preview.short_description = "Image"
