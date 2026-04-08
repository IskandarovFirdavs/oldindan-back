from django.conf import settings
from django.db import models
from restaurants.models import Branch
from layouts.models import Floor, Zone
from tables.models import Table

User = settings.AUTH_USER_MODEL


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("checked_in", "Checked In"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
        ("no_show", "No Show"),
    ]

    SOURCE_CHOICES = [
        ("app", "App"),
        ("partner_manual", "Partner Manual"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    floor = models.ForeignKey(
        Floor,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    guest_count = models.PositiveIntegerField()
    children_count = models.PositiveIntegerField(default=0)

    booking_start = models.DateTimeField()
    booking_end = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="app")

    special_request = models.TextField(blank=True)

    created_by_staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_bookings_created"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-booking_start", "-id"]
        indexes = [
            models.Index(fields=["branch", "booking_start"]),
            models.Index(fields=["table", "booking_start"]),
            models.Index(fields=["user", "booking_start"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.branch.name} - {self.table.name} - {self.booking_start}"


class BookingStatusLog(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="status_logs"
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    note = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.booking_id}: {self.old_status} -> {self.new_status}"