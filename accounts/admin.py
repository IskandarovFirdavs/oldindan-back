from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TelegramOTP, UserCreationAudit

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "phone", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("phone", "email", "first_name", "last_name")
    ordering = ("id",)


    fieldsets = (
        (None, {"fields": ("phone", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "bio", "avatar")}),
        ("Role & status", {"fields": ("role", "is_phone_verified", "is_email_verified", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "email", "password1", "password2", "role", "is_staff", "is_superuser"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")


@admin.register(TelegramOTP)
class TelegramOTPAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "purpose", "code", "is_used", "expires_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("phone", "code")


@admin.register(UserCreationAudit)
class UserCreationAuditAdmin(admin.ModelAdmin):
    list_display = ("id", "creator", "created_user", "created_at")