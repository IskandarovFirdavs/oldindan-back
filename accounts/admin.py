from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User, TelegramOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "role_badge", "phone", "email", "full_name", "branch", "is_active", "created_at")
    list_filter = ("role", "is_active", "branch")
    search_fields = ("phone", "email", "first_name", "last_name")
    ordering = ("-created_at",)

    fieldsets = (
        ("🔑 Login", {"fields": ("phone", "email", "password")}),
        ("👤 Personal", {"fields": ("first_name", "last_name", "bio", "avatar")}),
        ("🏷️ Role & Branch", {"fields": ("role", "branch")}),
        ("✅ Status", {"fields": ("is_phone_verified", "is_email_verified", "is_active", "is_staff", "is_superuser")}),
        ("🔒 Permissions", {"classes": ("collapse",), "fields": ("groups", "user_permissions")}),
        ("📅 Dates", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "email", "first_name", "last_name", "password1", "password2", "role", "branch", "is_active", "is_staff", "is_superuser"),
        }),
    )

    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("groups", "user_permissions")

    def role_badge(self, obj):
        colors = {
            "consumer": "#6c757d",
            "owner": "#198754",
            "manager": "#0d6efd",
            "receptionist": "#6610f2",
            "superadmin": "#dc3545",
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color, obj.get_role_display(),
        )
    role_badge.short_description = "Role"


@admin.register(TelegramOTP)
class TelegramOTPAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "purpose", "masked_code", "is_used", "attempt_count", "status_badge", "expires_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("phone",)

    def masked_code(self, obj):
        return f"{'*' * 4}{obj.code[-2:]}"
    masked_code.short_description = "Code"

    def status_badge(self, obj):
        from django.utils import timezone
        if obj.is_used:
            color, label = "#6c757d", "Used"
        elif timezone.now() > obj.expires_at:
            color, label = "#dc3545", "Expired"
        elif obj.attempt_count >= obj.max_attempts:
            color, label = "#fd7e14", "Blocked"
        else:
            color, label = "#198754", "Active"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, label,
        )
    status_badge.short_description = "Status"