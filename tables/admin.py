from django.contrib import admin
from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "branch",
        "floor",
        "zone",
        "seats",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "branch", "floor", "zone")
    search_fields = (
        "name",
        "branch__name",
        "floor__name",
        "zone__name",
    )