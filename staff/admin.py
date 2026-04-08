from django.contrib import admin
from .models import BranchStaff


@admin.register(BranchStaff)
class BranchStaffAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "branch", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "branch")
    search_fields = (
        "user__phone",
        "user__email",
        "user__first_name",
        "user__last_name",
        "branch__name",
    )