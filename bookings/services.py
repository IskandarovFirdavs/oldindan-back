from django.db import transaction
from django.utils import timezone
from .models import Booking, BookingStatusLog
from notifications.services import create_notification
from notifications.models import Notification

ACTIVE_BOOKING_STATUSES = ["pending", "confirmed", "checked_in"]


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


def validate_booking_relations(branch, floor, zone, table):
    if floor.branch_id != branch.id:
        raise ValueError("Floor shu branchga tegishli emas")

    if zone and zone.floor_id != floor.id:
        raise ValueError("Zone shu floorga tegishli emas")

    if table.branch_id != branch.id:
        raise ValueError("Table shu branchga tegishli emas")

    if table.floor_id != floor.id:
        raise ValueError("Table shu floorga tegishli emas")

    if zone and table.zone_id != zone.id:
        raise ValueError("Table shu zonega tegishli emas")


def validate_booking_time(booking_start, booking_end):
    now = timezone.now()
    if booking_start >= booking_end:
        raise ValueError("Booking start enddan kichik bo‘lishi kerak")

    if booking_start < now:
        raise ValueError("O‘tgan vaqtga booking qilib bo‘lmaydi")


@transaction.atomic
def create_booking(
    *,
    user,
    branch,
    floor,
    zone,
    table,
    guest_count,
    children_count,
    booking_start,
    booking_end,
    special_request="",
    source="app",
    created_by_staff=None,
):
    validate_booking_relations(branch, floor, zone, table)
    validate_booking_time(booking_start, booking_end)

    if not table.is_active:
        raise ValueError("Table faol emas")

    if guest_count <= 0:
        raise ValueError("Guest count 0 dan katta bo‘lishi kerak")

    if guest_count > table.seats:
        raise ValueError("Bu stolga buncha odam sig‘maydi")

    if not is_table_available(table, booking_start, booking_end):
        raise ValueError("Bu stol shu vaqtda band")

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
        status="pending" if source == "app" else "confirmed",
    )

    BookingStatusLog.objects.create(
        booking=booking,
        old_status="",
        new_status=booking.status,
        changed_by=created_by_staff if created_by_staff else user,
        note="Booking created"
    )

    # consumer notification
    create_notification(
        user=user,
        type=Notification.Type.BOOKING_CREATED,
        title="Bron yaratildi",
        message=f"{branch.name} da bron yaratildi",
        data={"booking_id": booking.id}
    )

    # owner notification
    if hasattr(branch, 'brand') and branch.brand and branch.brand.owner:
        owner = branch.brand.owner
        create_notification(
            user=owner,
            type=Notification.Type.BOOKING_CREATED,
            title="Yangi bron",
            message=f"{branch.name} da yangi bron",
            data={"booking_id": booking.id}
        )

    return booking


@transaction.atomic
def cancel_booking(*, booking, changed_by, note=""):
    old_status = booking.status
    if booking.status in ["completed", "canceled", "no_show"]:
        raise ValueError("Bu bookingni bekor qilib bo‘lmaydi")

    booking.status = "canceled"
    booking.save(update_fields=["status", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status=old_status,
        new_status="canceled",
        changed_by=changed_by,
        note=note or "Booking canceled"
    )

    # notification
    create_notification(
        user=booking.user,
        type=Notification.Type.BOOKING_CANCELED,
        title="Bron bekor qilindi",
        message="Sizning broningiz bekor qilindi",
        data={"booking_id": booking.id}
    )

    return booking


@transaction.atomic
def update_booking_status(*, booking, new_status, changed_by, note=""):
    allowed = ["pending", "confirmed", "checked_in", "completed", "canceled", "no_show"]
    if new_status not in allowed:
        raise ValueError("Noto‘g‘ri status")

    old_status = booking.status
    booking.status = new_status
    booking.save(update_fields=["status", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        note=note
    )

    # notification when status changes to confirmed
    if new_status == "confirmed":
        create_notification(
            user=booking.user,
            type=Notification.Type.BOOKING_CONFIRMED,
            title="Bron tasdiqlandi",
            message="Sizning broningiz tasdiqlandi",
            data={"booking_id": booking.id}
        )

    return booking


def send_booking_telegram_notification(booking, text):
    # HOZIRCHA PLACEHOLDER
    # keyin telegram bot service shu yerga ulanadi
    print(f"[TELEGRAM BOOKING] booking={booking.id} text={text}")