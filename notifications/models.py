from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        BOOKING_CREATED = "booking_created", "Bron yaratildi"
        BOOKING_CANCELED = "booking_canceled", "Bron bekor qilindi"
        BOOKING_CONFIRMED = "booking_confirmed", "Bron tasdiqlandi"
        BOOKING_UPDATED = "booking_updated", "Bron yangilandi"
        BOOKING_CHECKED_IN = "booking_checked_in", "Bron faollashtirildi"
        BOOKING_COMPLETED = "booking_completed", "Bron yakunlandi"
        BOOKING_NO_SHOW = "booking_no_show", "Kelmagan"
        SYSTEM = "system", "Tizim xabari"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=50, choices=Type.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"