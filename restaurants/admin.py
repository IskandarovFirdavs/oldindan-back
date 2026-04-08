from django.contrib import admin
from .models import RestaurantBrand, Branch, BranchImage


class BranchImageInline(admin.TabularInline):
    model = BranchImage
    extra = 1


@admin.register(RestaurantBrand)
class RestaurantBrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "slug", "created_at")
    search_fields = ("name", "slug", "owner__email", "owner__phone")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "brand",
        "phone",
        "is_active",
        "deposit_enabled",
        "deposit_amount",
        "service_fee",
    )
    list_filter = ("is_active", "deposit_enabled", "brand")
    search_fields = ("name", "slug", "address", "phone", "brand__name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BranchImageInline]


@admin.register(BranchImage)
class BranchImageAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "sort_order", "created_at")
    list_filter = ("branch",)