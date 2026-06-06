"""
Booking business logic — OLDINDAN platform.

SLOT SYSTEM (new):
  - Bookings happen in 30-minute blocks aligned to the branch's working hours.
    Example: branch opens 10:00, so slots are 10:00-10:30, 10:30-11:00, etc.
  - User picks one or more CONSECUTIVE slots (max 6 = 3 hours total).
  - Frontend shows green (available) / red (booked) for each slot.
  - booking_start = first selected slot start
  - booking_end   = last selected slot end
  - Minimum advance: 1 hour before booking_start
  - Maximum duration: 3 hours (6 × 30-min slots)
  - NO cleaning time between bookings.
  - NO minimum/maximum duration validation beyond the 30-min slot grid + 3h max.

BOOKING NUMBER:
  - Each booking gets a unique #XXXXXX code generated on save.
  - Receptionist uses this to check in the guest.

STATUS FLOW:
  pending  → confirmed (auto if branch.auto_confirm=True, else partner manually)
           → canceled (by partner with reason, or by consumer)
  confirmed → checked_in (receptionist scans/enters booking number)
            → canceled (with reason)
            → no_show (auto after grace period)
  checked_in → completed (receptionist marks when guest pays & leaves)
             → canceled
  completed → (terminal)
  canceled  → (terminal)
  no_show   → (terminal)
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
# 3. TIME VALIDATION (slot-based system)
# ============================================================

def _parse_time(value: str) -> time:
    """Parse 'HH:MM' string — always use this, never string comparison."""
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid working hours format: '{value}'. Expected 'HH:MM'.")


def _align_to_slot(dt) -> bool:
    """Returns True if dt is aligned to a 30-minute boundary (:00 or :30)."""
    return dt.minute in (0, 30) and dt.second == 0 and dt.microsecond == 0


def validate_basic_time(booking_start, booking_end):
    now = timezone.now()
    if booking_start >= booking_end:
        raise ValueError("Start time must be before end time.")
    if booking_start < now:
        raise ValueError("Cannot book in the past.")
    if booking_start > now + timedelta(days=30):
        raise ValueError("Cannot book more than 30 days in advance.")


def validate_slot_alignment(booking_start, booking_end):
    """Both start and end must be on 30-minute boundaries."""
    if not _align_to_slot(booking_start):
        raise ValueError(
            "Booking start must be on a 30-minute boundary (e.g. 10:00, 10:30, 11:00)."
        )
    if not _align_to_slot(booking_end):
        raise ValueError(
            "Booking end must be on a 30-minute boundary (e.g. 10:30, 11:00, 11:30)."
        )


def validate_min_advance(booking_start):
    """Booking must be made at least 1 hour before the slot starts."""
    if booking_start < timezone.now() + timedelta(hours=1):
        raise ValueError("Booking must be made at least 1 hour in advance.")


def validate_duration(booking_start, booking_end):
    """Minimum 30 min (1 slot), maximum 3 hours (6 slots)."""
    total_minutes = int((booking_end - booking_start).total_seconds() // 60)
    if total_minutes < 30:
        raise ValueError("Minimum booking duration is 30 minutes (1 slot).")
    if total_minutes > 180:
        raise ValueError(
            f"Maximum booking duration is 3 hours (180 minutes). "
            f"You selected {total_minutes} minutes."
        )


def validate_working_hours(booking_start, booking_end, branch):
    """
    booking_start and booking_end must be within branch working hours.
    working_hours format: {"mon": ["10:00", "22:00"], ...}
    """
    weekday       = booking_start.strftime("%a").lower()
    working_hours = branch.working_hours or {}

    if weekday not in working_hours:
        raise ValueError(f"{branch.name} is closed on {booking_start.strftime('%A')}.")

    work_start_str, work_end_str = working_hours[weekday]
    work_start_t = _parse_time(work_start_str)
    work_end_t   = _parse_time(work_end_str)

    local_tz        = timezone.get_current_timezone()
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
            f"Booking end ({booking_end_t.strftime('%H:%M')}) "
            f"is after closing time ({work_end_str})."
        )


def validate_booking_time(booking_start, booking_end, branch, table=None):
    """Single entry point for all time-related validation."""
    validate_basic_time(booking_start, booking_end)
    validate_slot_alignment(booking_start, booking_end)
    validate_min_advance(booking_start)
    validate_duration(booking_start, booking_end)
    validate_working_hours(booking_start, booking_end, branch)


# ============================================================
# 4. CAPACITY VALIDATION
# ============================================================

def validate_booking_capacity(guest_count, table):
    if guest_count <= 0:
        raise ValueError("Guest count must be greater than 0.")
    if guest_count > table.seats:
        raise ValueError(f"This table seats {table.seats}. You requested {guest_count}.")


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
# 6. SLOT GRID — for the booking UI
# ============================================================

def get_slots_with_status(table, branch, date) -> list[dict]:
    """
    Returns all 30-minute slots for the given branch/date, each marked as:
      - available  (green)
      - booked     (red — occupied by an active booking)
      - past       (grey — already passed, cannot book)
      - closed     (grey — outside working hours)

    Example response item:
      {"start": "10:00", "end": "10:30", "status": "available", "booking_id": null}

    The frontend uses this to render the slot grid.
    """
    local_tz      = timezone.get_current_timezone()
    now           = timezone.now()
    cutoff        = now + timedelta(hours=1)   # 1-hour advance rule

    weekday       = date.strftime("%a").lower()
    working_hours = branch.working_hours or {}

    if weekday not in working_hours:
        return []

    work_start_str, work_end_str = working_hours[weekday]
    work_start_t = _parse_time(work_start_str)
    work_end_t   = _parse_time(work_end_str)

    # Build all 30-min slots from open to close
    slot_cursor = timezone.make_aware(datetime.combine(date, work_start_t), local_tz)
    window_end  = timezone.make_aware(datetime.combine(date, work_end_t),   local_tz)

    # Load all active bookings for this table on this date once
    booked_intervals = list(
        Booking.objects.filter(
            table=table,
            status__in=ACTIVE_BOOKING_STATUSES,
            booking_start__date=date,
        ).values("id", "booking_start", "booking_end")
    )

    slots = []
    while slot_cursor + timedelta(minutes=30) <= window_end:
        slot_end = slot_cursor + timedelta(minutes=30)

        # Check if slot is in the past or within the 1-hour advance window
        if slot_cursor < cutoff:
            slot_status  = "past"
            slot_booking = None
        else:
            # Check if any active booking overlaps this slot
            overlapping = None
            for b in booked_intervals:
                if slot_cursor < b["booking_end"] and slot_end > b["booking_start"]:
                    overlapping = b
                    break

            if overlapping:
                slot_status  = "booked"
                slot_booking = overlapping["id"]
            else:
                slot_status  = "available"
                slot_booking = None

        slots.append({
            "start":      slot_cursor.astimezone(local_tz).strftime("%H:%M"),
            "end":        slot_end.astimezone(local_tz).strftime("%H:%M"),
            "status":     slot_status,      # "available" | "booked" | "past"
            "booking_id": slot_booking,
        })
        slot_cursor = slot_end

    return slots


def get_available_slots(table, branch, date, duration_minutes: int = 60) -> list[str]:
    """
    Simple list of available start times. Used by the old available-slots endpoint.
    """
    all_slots = get_slots_with_status(table, branch, date)
    return [s["start"] for s in all_slots if s["status"] == "available"]


# ============================================================
# 7. CREATE BOOKING
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
    select_for_update() prevents double-booking race conditions.
    Auto-confirms if branch.auto_confirm is True.
    """
    validate_booking_relations(branch, floor, zone, table)

    if not table.is_active:
        raise ValueError("This table is not active.")

    validate_booking_time(booking_start, booking_end, branch, table)
    validate_booking_capacity(guest_count, table)
    validate_children_count(children_count, guest_count)

    # ── RACE CONDITION FIX ────────────────────────────────────
    Booking.objects.select_for_update().filter(
        table=table,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_start__lt=booking_end,
        booking_end__gt=booking_start,
    ).exists()

    if not is_table_available(table, booking_start, booking_end):
        conflict = get_overlapping_bookings(table, booking_start, booking_end).first()
        if conflict:
            raise ValueError(
                f"This table is booked from {conflict.booking_start.strftime('%H:%M')} "
                f"to {conflict.booking_end.strftime('%H:%M')}. Please choose a different slot."
            )
        raise ValueError("This table is not available at the selected time.")

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

    # Auto-confirm if branch is set to auto-confirm OR it's a partner manual booking
    if branch.auto_confirm or source == "partner_manual":
        initial_status = "confirmed"
    else:
        initial_status = "pending"

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
        note="Booking created" + (" (auto-confirmed)" if initial_status == "confirmed" else ""),
    )

    # Notify guest
    create_notification(
        user=user,
        type=Notification.Type.BOOKING_CREATED,
        title="Booking created ✅",
        message=(
            f"Your booking #{booking.booking_number} at {branch.name} "
            f"for {booking_start.strftime('%d.%m.%Y %H:%M')}–{booking_end.strftime('%H:%M')} "
            f"has been {'confirmed' if initial_status == 'confirmed' else 'received and is pending confirmation'}."
        ),
        data={"booking_id": booking.id, "booking_number": booking.booking_number},
    )

    # Notify branch owner
    if (
        hasattr(branch, "brand")
        and branch.brand
        and branch.brand.owner
        and branch.brand.owner != user
    ):
        create_notification(
            user=branch.brand.owner,
            type=Notification.Type.BOOKING_CREATED,
            title="New booking 🔔",
            message=(
                f"New booking #{booking.booking_number} at {branch.name} "
                f"for {booking_start.strftime('%d.%m %H:%M')}–{booking_end.strftime('%H:%M')}. "
                + ("Auto-confirmed." if initial_status == "confirmed" else "Awaiting your confirmation.")
            ),
            data={"booking_id": booking.id, "booking_number": booking.booking_number},
        )

    return booking


# ============================================================
# 8. CHECK-IN BY BOOKING NUMBER
# ============================================================

@transaction.atomic
def checkin_by_number(*, booking_number: str, branch, changed_by) -> Booking:
    """
    Receptionist enters/scans booking number to check in the guest.
    Only confirmed bookings at the correct branch can be checked in.
    """
    try:
        booking = Booking.objects.select_for_update().get(
            booking_number=booking_number.upper().strip()
        )
    except Booking.DoesNotExist:
        raise ValueError(f"No booking found with number #{booking_number}.")

    if booking.branch_id != branch.id:
        raise ValueError("This booking is not for your branch.")

    if booking.status != "confirmed":
        if booking.status == "checked_in":
            raise ValueError("Guest has already checked in.")
        raise ValueError(
            f"Cannot check in — booking status is '{booking.status}'. "
            f"Only confirmed bookings can be checked in."
        )

    booking.status = "checked_in"
    booking.save(update_fields=["status", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status="confirmed",
        new_status="checked_in",
        changed_by=changed_by,
        note="Checked in via booking number",
    )

    create_notification(
        user=booking.user,
        type=Notification.Type.BOOKING_CHECKED_IN,
        title="Welcome! 🎉",
        message=(
            f"You have been checked in at {booking.branch.name}. "
            f"Enjoy your time!"
        ),
        data={"booking_id": booking.id, "booking_number": booking.booking_number},
    )

    return booking


# ============================================================
# 9. CANCEL BOOKING
# ============================================================

@transaction.atomic
def cancel_booking(*, booking: Booking, changed_by, note: str = "") -> Booking:
    validate_cancel_allowed(booking)

    old_status     = booking.status
    booking.status = "canceled"
    if note:
        booking.cancel_reason = note
    booking.save(update_fields=["status", "cancel_reason", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status=old_status,
        new_status="canceled",
        changed_by=changed_by,
        note=note or "Cancelled",
    )

    create_notification(
        user=booking.user,
        type=Notification.Type.BOOKING_CANCELED,
        title="Booking cancelled ❌",
        message=(
            f"Your booking #{booking.booking_number} at {booking.branch.name} "
            f"has been cancelled."
            + (f" Reason: {note}" if note else "")
        ),
        data={"booking_id": booking.id, "booking_number": booking.booking_number},
    )
    return booking


# ============================================================
# 10. UPDATE STATUS (partner use)
# ============================================================

@transaction.atomic
def update_booking_status(
    *, booking: Booking, new_status: str, changed_by, note: str = ""
) -> Booking:
    validate_status_transition(booking.status, new_status)

    old_status     = booking.status
    booking.status = new_status

    # Store cancel reason if status is becoming 'canceled'
    if new_status == "canceled" and note:
        booking.cancel_reason = note

    booking.save(update_fields=["status", "cancel_reason", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        note=note,
    )

    _send_status_notification(booking, new_status, note)
    return booking


def _send_status_notification(booking: Booking, new_status: str, note: str = ""):
    _map = {
        "confirmed": (
            Notification.Type.BOOKING_CONFIRMED,
            "Booking confirmed ✅",
            f"Booking #{booking.booking_number} at {booking.branch.name} "
            f"on {booking.booking_start.strftime('%d.%m %H:%M')} has been confirmed.",
        ),
        "checked_in": (
            Notification.Type.BOOKING_CHECKED_IN,
            "Welcome! 🎉",
            f"You have checked in at {booking.branch.name}. Enjoy your time!",
        ),
        "completed": (
            Notification.Type.BOOKING_COMPLETED,
            "Visit completed 🙏",
            f"Thank you for visiting {booking.branch.name}!",
        ),
        "canceled": (
            Notification.Type.BOOKING_CANCELED,
            "Booking cancelled ❌",
            f"Booking #{booking.booking_number} has been cancelled."
            + (f" Reason: {note}" if note else ""),
        ),
        "no_show": (
            Notification.Type.BOOKING_NO_SHOW,
            "No-show recorded",
            f"You did not arrive for booking #{booking.booking_number}. "
            f"The booking has been closed.",
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
        data={"booking_id": booking.id, "booking_number": booking.booking_number},
    )


# ============================================================
# 11. NO-SHOW AUTO-TIMER (called by a periodic task or endpoint)
# ============================================================

def get_no_show_grace_minutes(booking: Booking) -> int:
    """
    Returns how many minutes after booking_start the venue can mark no-show.
    Rules:
      - Booking duration 30 min  → grace 10 min
      - Booking duration 60 min  → grace 20 min
      - Booking duration > 60 min → grace 30 min
    """
    duration_minutes = int(
        (booking.booking_end - booking.booking_start).total_seconds() // 60
    )
    if duration_minutes <= 30:
        return 10
    elif duration_minutes <= 60:
        return 20
    else:
        return 30


def can_mark_no_show(booking: Booking) -> bool:
    """
    Returns True if the booking can be marked no-show now.
    Requires: status=confirmed AND grace period has passed.
    """
    if booking.status != "confirmed":
        return False
    grace     = timedelta(minutes=get_no_show_grace_minutes(booking))
    threshold = booking.booking_start + grace
    return timezone.now() >= threshold