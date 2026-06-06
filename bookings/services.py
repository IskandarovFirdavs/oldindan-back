"""
Booking business logic.

Rules:
  - Serializer validates field FORMAT only (type, required, min/max).
  - All business rules live HERE — working hours, overlap, capacity, cleaning.
  - create_booking() is the ONLY place that writes a Booking row.
  - select_for_update() prevents the race condition where two simultaneous
    requests both pass the availability check and both create a booking for
    the same table at the same time.
"""
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from notifications.models import Notification
from notifications.services import create_notification

from .models import Booking, BookingStatusLog

ACTIVE_BOOKING_STATUSES = ["pending", "confirmed", "checked_in"]


# ============================================================
# 1. TABLE AVAILABILITY
# ============================================================

def get_overlapping_bookings(table, booking_start, booking_end, exclude_booking_id=None):
    qs = Booking.objects.filter(
        table=table,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_start__lt=booking_end,
        booking_end__gt=booking_start,
    )
    if exclude_booking_id:
        qs = qs.exclude(id=exclude_booking_id)
    return qs


def is_table_available(table, booking_start, booking_end, exclude_booking_id=None):
    return not get_overlapping_bookings(
        table=table,
        booking_start=booking_start,
        booking_end=booking_end,
        exclude_booking_id=exclude_booking_id,
    ).exists()


# ============================================================
# 2. RELATION VALIDATION
# ============================================================

def validate_booking_relations(branch, floor, zone, table):
    errors = []
    if floor.branch_id != branch.id:
        errors.append("Floor does not belong to this branch.")
    if zone and zone.floor_id != floor.id:
        errors.append("Zone does not belong to this floor.")
    if table.branch_id != branch.id:
        errors.append("Table does not belong to this branch.")
    if table.floor_id != floor.id:
        errors.append("Table does not belong to this floor.")
    if zone and table.zone_id != zone.id:
        errors.append("Table does not belong to this zone.")
    if errors:
        raise ValueError("; ".join(errors))


# ============================================================
# 3. TIME VALIDATION
# ============================================================

def _parse_time(value: str) -> time:
    """Parse 'HH:MM' or 'H:MM' — never use string comparison for time."""
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid working hours format: '{value}'. Expected 'HH:MM'."
        )


def validate_basic_time(booking_start, booking_end):
    now = timezone.now()
    if booking_start >= booking_end:
        raise ValueError("Start time must be before end time.")
    if booking_start < now:
        raise ValueError("Cannot book in the past.")
    if booking_start > now + timedelta(days=30):
        raise ValueError("Cannot book more than 30 days in advance.")


def validate_min_advance(booking_start):
    if booking_start < timezone.now() + timedelta(hours=2):
        raise ValueError("Booking must be made at least 2 hours in advance.")


def validate_duration(booking_start, booking_end):
    total_minutes = int((booking_end - booking_start).total_seconds() // 60)
    if total_minutes < 30:
        raise ValueError(
            f"Minimum booking duration is 30 minutes. You entered {total_minutes} minutes."
        )
    if total_minutes > 240:
        raise ValueError(
            f"Maximum booking duration is 4 hours (240 minutes). You entered {total_minutes} minutes."
        )


def validate_working_hours(booking_start, booking_end, branch):
    """
    Checks that booking falls within branch working hours.
    working_hours format: {"mon": ["09:00", "22:00"], ...}
    Keys match Python strftime('%a').lower(): mon, tue, wed, thu, fri, sat, sun.
    """
    weekday = booking_start.strftime("%a").lower()
    working_hours = branch.working_hours or {}

    if weekday not in working_hours:
        raise ValueError(
            f"{branch.name} is closed on {booking_start.strftime('%A')}."
        )

    work_start_str, work_end_str = working_hours[weekday]
    work_start_t = _parse_time(work_start_str)
    work_end_t   = _parse_time(work_end_str)

    local_tz       = timezone.get_current_timezone()
    booking_start_t = booking_start.astimezone(local_tz).time()
    booking_end_t   = booking_end.astimezone(local_tz).time()

    if booking_start_t < work_start_t:
        raise ValueError(
            f"{branch.name} opens at {work_start_str}. "
            f"You selected {booking_start_t.strftime('%H:%M')}."
        )
    if booking_start_t >= work_end_t:
        raise ValueError(
            f"{branch.name} closes at {work_end_str}. "
            f"You selected {booking_start_t.strftime('%H:%M')}."
        )
    if booking_end_t > work_end_t:
        raise ValueError(
            f"Booking end time ({booking_end_t.strftime('%H:%M')}) is after closing time ({work_end_str})."
        )


def validate_booking_hours(booking_start, branch):
    """
    Optional: branch may restrict when bookings can START.
    booking_hours format: {"mon": ["10:00", "20:00"], ...}
    Empty means no restriction.
    """
    weekday = booking_start.strftime("%a").lower()
    booking_hours = branch.booking_hours or {}

    if not booking_hours or weekday not in booking_hours:
        return

    book_start_str, book_end_str = booking_hours[weekday]
    book_start_t = _parse_time(book_start_str)
    book_end_t   = _parse_time(book_end_str)
    booking_start_t = booking_start.astimezone(timezone.get_current_timezone()).time()

    if booking_start_t < book_start_t:
        raise ValueError(
            f"Bookings on this day start from {book_start_str}."
        )
    if booking_start_t >= book_end_t:
        raise ValueError(
            f"Bookings on this day are accepted until {book_end_str}."
        )


def validate_cleaning_time(table, booking_start, booking_end, exclude_booking_id=None):
    """15-minute cleaning gap required between consecutive bookings."""
    cleaning = timedelta(minutes=15)

    prev_qs = Booking.objects.filter(
        table=table,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_end__lte=booking_start,
        booking_end__gt=booking_start - cleaning,
    )
    if exclude_booking_id:
        prev_qs = prev_qs.exclude(id=exclude_booking_id)

    if prev_qs.exists():
        prev = prev_qs.order_by("-booking_end").first()
        needed_start = prev.booking_end + cleaning
        raise ValueError(
            f"15-minute cleaning time required. "
            f"Previous booking ends at {prev.booking_end.strftime('%H:%M')}. "
            f"Earliest available start: {needed_start.strftime('%H:%M')}."
        )

    next_qs = Booking.objects.filter(
        table=table,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_start__gte=booking_end,
        booking_start__lt=booking_end + cleaning,
    )
    if exclude_booking_id:
        next_qs = next_qs.exclude(id=exclude_booking_id)

    if next_qs.exists():
        nxt = next_qs.order_by("booking_start").first()
        latest_end = nxt.booking_start - cleaning
        raise ValueError(
            f"15-minute cleaning time required. "
            f"Next booking starts at {nxt.booking_start.strftime('%H:%M')}. "
            f"Your booking must end by {latest_end.strftime('%H:%M')}."
        )


def validate_booking_time(booking_start, booking_end, branch, table):
    """Single entry point for all time-related validation."""
    validate_basic_time(booking_start, booking_end)
    validate_min_advance(booking_start)
    validate_duration(booking_start, booking_end)
    validate_working_hours(booking_start, booking_end, branch)
    validate_booking_hours(booking_start, branch)


# ============================================================
# 4. CAPACITY VALIDATION
# ============================================================

def validate_booking_capacity(guest_count, table):
    if guest_count <= 0:
        raise ValueError("Guest count must be greater than 0.")
    if guest_count > table.seats:
        raise ValueError(
            f"This table seats {table.seats}. You requested {guest_count}."
        )


def validate_children_count(children_count, guest_count):
    if children_count < 0:
        raise ValueError("Children count cannot be negative.")
    if children_count > guest_count * 3:
        raise ValueError(
            f"Children count ({children_count}) cannot exceed 3× the guest count."
        )


# ============================================================
# 5. STATUS TRANSITION
# ============================================================

_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending":    ["confirmed", "canceled"],
    "confirmed":  ["checked_in", "canceled", "no_show"],
    "checked_in": ["completed", "canceled"],
    "completed":  [],
    "canceled":   [],
    "no_show":    [],
}


def validate_status_transition(old_status: str, new_status: str):
    allowed = _ALLOWED_TRANSITIONS.get(old_status)
    if allowed is None:
        raise ValueError(f"Unknown status: '{old_status}'.")
    if new_status not in allowed:
        if allowed:
            raise ValueError(
                f"Cannot transition from '{old_status}' to '{new_status}'. "
                f"Allowed: {', '.join(allowed)}."
            )
        raise ValueError(f"Cannot change status from '{old_status}'.")


def validate_cancel_allowed(booking):
    if booking.status in ["completed", "canceled", "no_show"]:
        raise ValueError(f"Cannot cancel a booking with status '{booking.status}'.")
    minutes_until_start = (booking.booking_start - timezone.now()).total_seconds() / 60
    if 0 < minutes_until_start < 15:
        raise ValueError(
            f"Cannot cancel — booking starts in {int(minutes_until_start)} minutes."
        )


# ============================================================
# 6. CREATE BOOKING  ← race condition fixed with select_for_update
# ============================================================

@transaction.atomic
def create_booking(
    *,
    user,
    branch,
    floor,
    zone,
    table,
    guest_count: int,
    children_count: int,
    booking_start,
    booking_end,
    special_request: str = "",
    source: str = "app",
    created_by_staff=None,
) -> Booking:
    """
    Creates a booking. All business rules are enforced here.
    select_for_update() locks overlapping booking rows so two simultaneous
    requests cannot both pass the availability check and create a double booking.
    """
    validate_booking_relations(branch, floor, zone, table)

    if not table.is_active:
        raise ValueError("This table is not active.")

    validate_booking_time(booking_start, booking_end, branch, table)
    validate_booking_capacity(guest_count, table)
    validate_children_count(children_count, guest_count)

    # ── RACE CONDITION FIX ───────────────────────────────────
    # Lock any existing active bookings for this table that overlap our window.
    # If two requests arrive simultaneously, the second one blocks here until
    # the first transaction commits, then re-reads and finds the conflict.
    Booking.objects.select_for_update().filter(
        table=table,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_start__lt=booking_end,
        booking_end__gt=booking_start,
    ).exists()  # Forces the lock to be acquired

    # Now re-check availability with the lock held
    if not is_table_available(table, booking_start, booking_end):
        conflict = get_overlapping_bookings(table, booking_start, booking_end).first()
        if conflict:
            raise ValueError(
                f"This table is booked from {conflict.booking_start.strftime('%H:%M')} "
                f"to {conflict.booking_end.strftime('%H:%M')}. Please choose a different time."
            )
        raise ValueError("This table is not available at the selected time.")

    validate_cleaning_time(table, booking_start, booking_end)

    # One active booking per user at a time
    if Booking.objects.filter(
        user=user,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_start__lt=booking_end,
        booking_end__gt=booking_start,
    ).exists():
        raise ValueError(
            "You already have an active booking during this time. "
            "Only one booking at a time is allowed."
        )

    initial_status = "pending" if source == "app" else "confirmed"

    booking = Booking.objects.create(
        user=user,
        branch=branch,
        floor=floor,
        zone=zone,
        table=table,
        guest_count=guest_count,
        children_count=children_count,
        booking_start=booking_start,
        booking_end=booking_end,
        special_request=special_request,
        source=source,
        created_by_staff=created_by_staff,
        status=initial_status,
    )

    BookingStatusLog.objects.create(
        booking=booking,
        old_status="",
        new_status=initial_status,
        changed_by=created_by_staff or user,
        note="Booking created",
    )

    # Notifications
    create_notification(
        user=user,
        type=Notification.Type.BOOKING_CREATED,
        title="Booking created",
        message=(
            f"Your booking at {branch.name} for "
            f"{booking_start.strftime('%d.%m.%Y %H:%M')} has been created."
        ),
        data={"booking_id": booking.id},
    )
    if (
        hasattr(branch, "brand")
        and branch.brand
        and branch.brand.owner
        and branch.brand.owner != user
    ):
        create_notification(
            user=branch.brand.owner,
            type=Notification.Type.BOOKING_CREATED,
            title="New booking",
            message=(
                f"New booking at {branch.name} for "
                f"{booking_start.strftime('%d.%m.%Y %H:%M')}."
            ),
            data={"booking_id": booking.id},
        )

    return booking


# ============================================================
# 7. CANCEL BOOKING
# ============================================================

@transaction.atomic
def cancel_booking(*, booking: Booking, changed_by, note: str = "") -> Booking:
    validate_cancel_allowed(booking)

    old_status    = booking.status
    booking.status = "canceled"
    booking.save(update_fields=["status", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status=old_status,
        new_status="canceled",
        changed_by=changed_by,
        note=note or "Cancelled by user",
    )

    create_notification(
        user=booking.user,
        type=Notification.Type.BOOKING_CANCELED,
        title="Booking cancelled",
        message="Your booking has been cancelled." + (f" Reason: {note}" if note else ""),
        data={"booking_id": booking.id},
    )
    return booking


# ============================================================
# 8. UPDATE STATUS
# ============================================================

@transaction.atomic
def update_booking_status(
    *, booking: Booking, new_status: str, changed_by, note: str = ""
) -> Booking:
    validate_status_transition(booking.status, new_status)

    old_status     = booking.status
    booking.status = new_status
    booking.save(update_fields=["status", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        note=note,
    )

    _send_status_notification(booking, new_status)
    return booking


def _send_status_notification(booking: Booking, new_status: str):
    _map = {
        "confirmed": (
            Notification.Type.BOOKING_CONFIRMED,
            "Booking confirmed",
            f"Table #{booking.table.name}, {booking.booking_start.strftime('%H:%M')}.",
        ),
        "checked_in": (
            Notification.Type.BOOKING_CHECKED_IN,
            "Welcome!",
            "Your booking has been activated.",
        ),
        "completed": (
            Notification.Type.BOOKING_COMPLETED,
            "Booking completed",
            "Thank you for visiting us!",
        ),
        "no_show": (
            Notification.Type.BOOKING_NO_SHOW,
            "No-show recorded",
            "You did not arrive for your booking. The booking has been closed.",
        ),
    }
    if new_status not in _map:
        return
    notif_type, title, message = _map[new_status]
    create_notification(
        user=booking.user,
        type=notif_type,
        title=title,
        message=message,
        data={"booking_id": booking.id},
    )


# ============================================================
# 9. AVAILABLE SLOTS ENDPOINT HELPER
# ============================================================

def get_available_slots(
    table,
    branch,
    date,
    duration_minutes: int = 60,
) -> list[str]:
    """
    Returns a list of available start times (HH:MM) for a given table and date.
    Used by the available-slots endpoint.
    """
    from datetime import date as date_type

    local_tz  = timezone.get_current_timezone()
    cleaning  = timedelta(minutes=15)
    duration  = timedelta(minutes=duration_minutes)
    now       = timezone.now()

    # Determine operating window from working_hours
    weekday       = date.strftime("%a").lower()
    working_hours = branch.working_hours or {}

    if weekday not in working_hours:
        return []  # Branch closed on this day

    work_start_str, work_end_str = working_hours[weekday]
    work_start_t = _parse_time(work_start_str)
    work_end_t   = _parse_time(work_end_str)

    # Build candidate datetimes every 30 minutes
    slot_start = timezone.make_aware(
        datetime.combine(date, work_start_t), local_tz
    )
    window_end = timezone.make_aware(
        datetime.combine(date, work_end_t), local_tz
    )

    # Enforce 2-hour advance booking rule
    earliest_allowed = now + timedelta(hours=2)
    if slot_start < earliest_allowed:
        # Round up to next 30-min mark
        minutes_diff = int((earliest_allowed - slot_start).total_seconds() // 60)
        rounded_up   = ((minutes_diff + 29) // 30) * 30
        slot_start   = slot_start + timedelta(minutes=rounded_up)

    # Load all active bookings for this table on this date once
    bookings = list(
        Booking.objects.filter(
            table=table,
            status__in=ACTIVE_BOOKING_STATUSES,
            booking_start__date=date,
        ).order_by("booking_start")
    )

    available = []
    candidate = slot_start

    while candidate + duration <= window_end:
        candidate_end = candidate + duration

        # Check overlap with any existing booking (including cleaning buffer)
        conflict = False
        for b in bookings:
            # Booking is considered occupied if within cleaning distance
            if candidate < b.booking_end + cleaning and candidate_end > b.booking_start - cleaning:
                # Jump past this booking
                candidate = b.booking_end + cleaning
                conflict  = True
                break

        if not conflict:
            available.append(candidate.astimezone(local_tz).strftime("%H:%M"))
            candidate += timedelta(minutes=30)

    return available


def get_next_available_slot(table, start_time, duration_minutes: int = 60):
    """Returns the next free slot start time for a table from start_time onwards."""
    cleaning = timedelta(minutes=15)
    duration = timedelta(minutes=duration_minutes)

    bookings = (
        Booking.objects.filter(
            table=table,
            status__in=ACTIVE_BOOKING_STATUSES,
            booking_end__gte=start_time,
        ).order_by("booking_start")
    )

    candidate = start_time
    for b in bookings:
        if candidate + duration <= b.booking_start - cleaning:
            return candidate
        candidate = b.booking_end + cleaning

    return candidate


def can_extend_booking(booking: Booking, new_end) -> bool:
    if booking.status not in ["confirmed", "checked_in"]:
        raise ValueError(f"Cannot extend a booking with status '{booking.status}'.")
    if new_end <= booking.booking_end:
        raise ValueError("New end time must be after current end time.")
    if not is_table_available(
        booking.table, booking.booking_end, new_end, exclude_booking_id=booking.id
    ):
        raise ValueError("Table is occupied after your current booking ends.")
    return True