from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__phone', 'user__email', 'title')
    
    # message maydoni yo'qligi sababli, faqat mavjud maydonlarni ko'rsatish
    fields = ('user', 'type', 'title', 'is_read', 'data', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')