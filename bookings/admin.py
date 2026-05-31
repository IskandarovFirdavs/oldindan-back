from django.contrib import admin
from django.utils.html import format_html

from .models import Booking, BookingStatusLog


# ─── Inline: status log ──────────────────────────────────────
class BookingStatusLogInline(admin.TabularInline):
    model           = BookingStatusLog
    extra           = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "note", "created_at")
    fields          = ("old_status", "new_status", "changed_by", "note", "created_at")
    ordering        = ("created_at",)
    can_delete      = False
    verbose_name    = "Status change"
    verbose_name_plural = "Status history"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # ── list view ────────────────────────────────────────────
    list_display   = (
        "id",
        "user_link",
        "branch_link",
        "table",
        "booking_start",
        "booking_end",
        "guest_count",
        "status_badge",
        "source_badge",
        "created_at",
    )
    list_filter    = ("status", "source", "branch", "floor", "zone")
    search_fields  = (
        "user__phone", "user__email",
        "user__first_name", "user__last_name",
        "branch__name", "table__name",
    )
    date_hierarchy = "booking_start"
    ordering       = ("-booking_start",)
    list_per_page  = 40
    raw_id_fields  = ("user", "branch", "floor", "zone", "table", "created_by_staff")

    # ── form layout ──────────────────────────────────────────
    fieldsets = (
        ("🗓️ Booking info", {
            "fields": (
                "user", "branch", "floor", "zone", "table",
                "guest_count", "children_count",
                "booking_start", "booking_end",
                "special_request",
            ),
        }),
        ("📊 Status & Source", {
            "fields": ("status", "source", "created_by_staff"),
        }),
        ("📅 Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )
    readonly_fields = ("created_at", "updated_at")
    inlines         = [BookingStatusLogInline]

    # ── custom columns ───────────────────────────────────────
    def user_link(self, obj):
        url = f"/admin/accounts/user/{obj.user_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.user)
    user_link.short_description = "User"
    user_link.admin_order_field = "user"

    def branch_link(self, obj):
        url = f"/admin/restaurants/branch/{obj.branch_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.branch.name)
    branch_link.short_description = "Branch"
    branch_link.admin_order_field = "branch"

    def status_badge(self, obj):
        colors = {
            "pending":   ("#fff3cd", "#856404"),
            "confirmed": ("#d1e7dd", "#0a3622"),
            "checked_in": ("#cff4fc", "#055160"),
            "completed": ("#d1e7dd", "#0a3622"),
            "canceled":  ("#f8d7da", "#842029"),
            "no_show":   ("#e2e3e5", "#41464b"),
        }
        bg, fg = colors.get(obj.status, ("#e2e3e5", "#41464b"))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            bg, fg, obj.get_status_display(),
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def source_badge(self, obj):
        color = "#0d6efd" if obj.source == "app" else "#6610f2"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_source_display(),
        )
    source_badge.short_description = "Source"


@admin.register(BookingStatusLog)
class BookingStatusLogAdmin(admin.ModelAdmin):
    list_display   = (
        "id", "booking_link",
        "transition_arrow", "changed_by",
        "note", "created_at",
    )
    list_filter    = ("new_status", "old_status")
    search_fields  = ("booking__id", "changed_by__phone", "changed_by__email")
    readonly_fields = ("created_at",)
    ordering       = ("-created_at",)
    raw_id_fields  = ("booking", "changed_by")

    def booking_link(self, obj):
        url = f"/admin/bookings/booking/{obj.booking_id}/change/"
        return format_html('<a href="{}">Booking #{}</a>', url, obj.booking_id)
    booking_link.short_description = "Booking"

    def transition_arrow(self, obj):
        return format_html(
            '<code style="font-size:12px">{} → {}</code>',
            obj.old_status or "—", obj.new_status,
        )
    transition_arrow.short_description = "Transition"