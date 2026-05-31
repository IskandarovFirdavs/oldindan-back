from django.contrib import admin
from django.utils.html import format_html

from .models import RestaurantBrand, Branch, BranchImage


# ─── Inline: branch images ───────────────────────────────────
class BranchImageInline(admin.TabularInline):
    model          = BranchImage
    extra          = 1
    readonly_fields = ("image_preview",)
    fields         = ("image", "sort_order", "image_preview")
    ordering       = ("sort_order",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:4px"/>',
                obj.image.url,
            )
        return "—"
    image_preview.short_description = "Preview"


# ─── Inline: branches inside brand ───────────────────────────
class BranchInline(admin.TabularInline):
    model           = Branch
    extra           = 0
    fields          = ("name", "slug", "address", "is_active", "branch_link")
    readonly_fields = ("branch_link",)
    show_change_link = True

    def branch_link(self, obj):
        if obj.pk:
            url = f"/admin/restaurants/branch/{obj.pk}/change/"
            return format_html('<a href="{}">Edit →</a>', url)
        return "—"
    branch_link.short_description = ""


@admin.register(RestaurantBrand)
class RestaurantBrandAdmin(admin.ModelAdmin):
    list_display   = ("id", "logo_preview", "name", "owner_link", "slug", "branch_count", "created_at")
    search_fields  = ("name", "slug", "owner__email", "owner__phone")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields  = ("owner",)
    ordering       = ("-created_at",)
    inlines        = [BranchInline]

    fieldsets = (
        ("Brand info", {
            "fields": ("name", "slug", "owner", "logo", "description"),
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at",),
        }),
    )
    readonly_fields = ("created_at",)

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:4px"/>',
                obj.logo.url,
            )
        return "—"
    logo_preview.short_description = "Logo"

    def owner_link(self, obj):
        url = f"/admin/accounts/user/{obj.owner_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.owner)
    owner_link.short_description = "Owner"

    def branch_count(self, obj):
        count = obj.branches.count()
        return format_html(
            '<span style="font-weight:600">{}</span> branch{}',
            count, "es" if count != 1 else "",
        )
    branch_count.short_description = "Branches"


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display   = (
        "id", "name", "brand_link",
        "phone", "active_badge",
        "deposit_enabled", "deposit_amount", "service_fee",
        "created_at",
    )
    list_filter    = ("is_active", "deposit_enabled", "brand")
    search_fields  = ("name", "slug", "address", "phone", "brand__name")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields  = ("brand",)
    ordering       = ("-created_at",)
    inlines        = [BranchImageInline]

    fieldsets = (
        ("📍 Location", {
            "fields": ("brand", "name", "slug", "address", "latitude", "longitude", "phone"),
        }),
        ("🕐 Hours", {
            "description": (
                'Format: {"mon": ["09:00", "22:00"], "tue": [...], ...} '
                'Keys: mon tue wed thu fri sat sun'
            ),
            "fields": ("working_hours", "booking_hours"),
        }),
        ("💰 Pricing & Deposits", {
            "fields": ("service_fee", "deposit_enabled", "deposit_amount"),
        }),
        ("⚙️ Status", {
            "fields": ("is_active",),
        }),
        ("📅 Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    def brand_link(self, obj):
        url = f"/admin/restaurants/restaurantbrand/{obj.brand_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.brand.name)
    brand_link.short_description = "Brand"

    def active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background:#d1e7dd;color:#0a3622;padding:2px 8px;'
                'border-radius:4px;font-size:11px">Active</span>'
            )
        return format_html(
            '<span style="background:#f8d7da;color:#842029;padding:2px 8px;'
            'border-radius:4px;font-size:11px">Inactive</span>'
        )
    active_badge.short_description = "Status"
    active_badge.admin_order_field = "is_active"


@admin.register(BranchImage)
class BranchImageAdmin(admin.ModelAdmin):
    list_display   = ("id", "image_preview", "branch", "sort_order", "created_at")
    list_filter    = ("branch",)
    raw_id_fields  = ("branch",)
    ordering       = ("branch", "sort_order")

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:50px;border-radius:4px"/>',
                obj.image.url,
            )
        return "—"
    image_preview.short_description = "Preview"