import random
import string

from django.conf import settings
from django.db import models
from restaurants.models import Branch
from layouts.models import Floor, Zone
from tables.models import Table

User = settings.AUTH_USER_MODEL


def _generate_booking_number():
    """Generates a unique 6-character alphanumeric booking number like #A3X9K2."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending",    "Pending"),
        ("confirmed",  "Confirmed"),
        ("checked_in", "Checked In"),
        ("completed",  "Completed"),
        ("canceled",   "Canceled"),
        ("no_show",    "No Show"),
    ]

    SOURCE_CHOICES = [
        ("app",            "App"),
        ("partner_manual", "Partner Manual"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookings"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="bookings"
    )
    floor = models.ForeignKey(
        Floor, on_delete=models.CASCADE, related_name="bookings"
    )
    zone = models.ForeignKey(
        Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings"
    )
    table = models.ForeignKey(
        Table, on_delete=models.CASCADE, related_name="bookings"
    )

    # Unique booking reference shown to guest — e.g. #A3X9K2
    booking_number = models.CharField(max_length=6, unique=True, db_index=True)

    guest_count     = models.PositiveIntegerField()
    children_count  = models.PositiveIntegerField(default=0)

    booking_start = models.DateTimeField()
    booking_end   = models.DateTimeField()

    status  = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    source  = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="app")

    special_request = models.TextField(blank=True)
    cancel_reason   = models.TextField(blank=True)  # filled when status → canceled

    created_by_staff = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="manual_bookings_created"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-booking_start", "-id"]
        indexes = [
            models.Index(fields=["branch", "booking_start"]),
            models.Index(fields=["table",  "booking_start"]),
            models.Index(fields=["user",   "booking_start"]),
            models.Index(fields=["status"]),
            models.Index(fields=["booking_number"]),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate booking_number on creation
        if not self.booking_number:
            for _ in range(10):
                candidate = _generate_booking_number()
                if not Booking.objects.filter(booking_number=candidate).exists():
                    self.booking_number = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.booking_number} — {self.branch.name} {self.booking_start:%d.%m %H:%M}"


class BookingStatusLog(models.Model):
    booking    = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="status_logs")
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note       = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.booking_id}: {self.old_status} → {self.new_status}"


class Message(models.Model):
    """
    Real-time chat message between a guest (consumer) and the branch (partner).
    Each booking has its own chat thread.
    """
    booking    = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="messages")
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    text       = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes  = [models.Index(fields=["booking", "created_at"])]

    def __str__(self):
        return f"Booking #{self.booking.booking_number} — {self.sender}: {self.text[:40]}"