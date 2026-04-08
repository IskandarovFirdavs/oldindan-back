from django.contrib import admin
from .models import Booking, BookingStatusLog


class BookingStatusLogInline(admin.TabularInline):
    model = BookingStatusLog
    extra = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "note", "created_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "branch",
        "table",
        "booking_start",
        "booking_end",
        "guest_count",
        "status",
        "source",
    )
    list_filter = ("status", "source", "branch", "floor", "zone")
    search_fields = (
        "user__phone",
        "user__email",
        "branch__name",
        "table__name",
        "special_request",
    )
    inlines = [BookingStatusLogInline]


@admin.register(BookingStatusLog)
class BookingStatusLogAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("new_status",)