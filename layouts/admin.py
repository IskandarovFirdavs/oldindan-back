from django.contrib import admin
from .models import Floor, Zone, LayoutItem


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "branch", "sort_order", "is_active", "created_at")
    list_filter = ("is_active", "branch")
    search_fields = ("name", "branch__name")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "floor", "color", "sort_order", "is_active")
    list_filter = ("is_active", "floor__branch", "floor")
    search_fields = ("name", "floor__name", "floor__branch__name")


@admin.register(LayoutItem)
class LayoutItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "name",
        "floor",
        "zone",
        "x",
        "y",
        "width",
        "height",
        "is_active",
    )
    list_filter = ("type", "shape", "is_active", "floor__branch", "floor")
    search_fields = ("name", "floor__name", "floor__branch__name")