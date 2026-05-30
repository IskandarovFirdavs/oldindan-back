"""
Booking business logic — barcha validatsiya va yaratish shu yerda.

Qoidalar:
- Serializer faqat maydon darajasidagi validatsiya qiladi (format, required, tip).
- Biznes qoidalar (overlapping, ish vaqti, sig'im va h.k.) faqat shu modulda.
- create_booking() serializer tomonidan ishonchli ma'lumot qabul qiladi,
  shuning uchun serializer va service ikkalasida bir xil tekshiruv QILINMAYDI.
"""
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from notifications.models import Notification
from notifications.services import create_notification

from .models import Booking, BookingStatusLog

ACTIVE_BOOKING_STATUSES = ["pending", "confirmed", "checked_in"]


# ============================================================
# 1. STOL BANDLIGINI TEKSHIRISH
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
# 2. OBYEKTLAR MOSLIGI
# ============================================================

def validate_booking_relations(branch, floor, zone, table):
    errors = []

    if floor.branch_id != branch.id:
        errors.append("Qavat (floor) ushbu filialga tegishli emas.")

    if zone and zone.floor_id != floor.id:
        errors.append("Zona ushbu qavatga tegishli emas.")

    if table.branch_id != branch.id:
        errors.append("Stol ushbu filialga tegishli emas.")

    if table.floor_id != floor.id:
        errors.append("Stol ushbu qavatga tegishli emas.")

    if zone and table.zone_id != zone.id:
        errors.append("Stol ushbu zonaga tegishli emas.")

    if errors:
        raise ValueError("; ".join(errors))


# ============================================================
# 3. VAQT VALIDATSIYASI
# ============================================================

def _parse_time(value: str) -> time:
    """
    'HH:MM' yoki 'H:MM' formatdagi stringni datetime.time ga o'giradi.
    String taqqoslash ishlatilmaydi — bu xatolikka olib keladi.
    """
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except (ValueError, AttributeError):
        raise ValueError(f"Ish vaqti formati noto'g'ri: '{value}'. 'HH:MM' ko'rinishida bo'lishi kerak.")


def validate_basic_time(booking_start, booking_end):
    now = timezone.now()

    if booking_start >= booking_end:
        raise ValueError("Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak.")

    if booking_start < now:
        raise ValueError("O'tgan vaqtga bron qilib bo'lmaydi.")

    max_advance = now + timedelta(days=30)
    if booking_start > max_advance:
        raise ValueError("Bronni maksimal 30 kun oldin qilish mumkin.")


def validate_min_advance(booking_start):
    min_advance = timezone.now() + timedelta(hours=2)
    if booking_start < min_advance:
        raise ValueError("Bronni kamida 2 soat oldin qilish kerak.")


def validate_duration(booking_start, booking_end):
    duration = booking_end - booking_start
    total_minutes = int(duration.total_seconds() // 60)

    if total_minutes < 30:
        raise ValueError(
            f"Bron kamida 30 daqiqa bo'lishi kerak. Siz {total_minutes} daqiqa kiritdingiz."
        )

    max_minutes = 4 * 60
    if total_minutes > max_minutes:
        raise ValueError(
            f"Bron maksimal 4 soat (240 daqiqa) bo'lishi mumkin. Siz {total_minutes} daqiqa kiritdingiz."
        )


def validate_working_hours(booking_start, booking_end, branch):
    """
    Filial ish vaqtini tekshiradi.
    working_hours format: {{"mon": ["09:00", "22:00"], "tue": [...], ...}}
    Kalit — Python strftime '%a' bilan mos keladi: mon, tue, wed, thu, fri, sat, sun.
    """
    weekday = booking_start.strftime("%a").lower()  # "mon", "tue" ...
    working_hours = branch.working_hours or {}

    if weekday not in working_hours:
        raise ValueError(f"{branch.name} {booking_start.strftime('%A')} kuni ishlamaydi.")

    work_start_str, work_end_str = working_hours[weekday]

    # String taqqoslash emas — time obyektlari taqqoslanadi
    work_start_t = _parse_time(work_start_str)
    work_end_t = _parse_time(work_end_str)
    booking_start_t = booking_start.astimezone(timezone.get_current_timezone()).time()
    booking_end_t = booking_end.astimezone(timezone.get_current_timezone()).time()

    if booking_start_t < work_start_t:
        raise ValueError(
            f"Filial soat {work_start_str} da ochiladi. Siz {booking_start_t.strftime('%H:%M')} da bron qilmoqchisiz."
        )

    if booking_start_t >= work_end_t:
        raise ValueError(
            f"Filial soat {work_end_str} da yopiladi. Siz {booking_start_t.strftime('%H:%M')} da bron qilmoqchisiz."
        )

    if booking_end_t > work_end_t:
        raise ValueError(
            f"Bron tugash vaqti ({booking_end_t.strftime('%H:%M')}) filial yopilish vaqtidan "
            f"({work_end_str}) keyin. Iltimos, vaqtni o'zgartiring."
        )


def validate_booking_hours(booking_start, branch):
    """
    Ixtiyoriy: filial qaysi vaqtda bron qabul qilishini cheklash.
    booking_hours format: {{"mon": ["10:00", "20:00"], ...}}
    Bo'sh bo'lsa cheklov yo'q.
    """
    weekday = booking_start.strftime("%a").lower()
    booking_hours = branch.booking_hours or {}

    if not booking_hours or weekday not in booking_hours:
        return

    book_start_str, book_end_str = booking_hours[weekday]
    book_start_t = _parse_time(book_start_str)
    book_end_t = _parse_time(book_end_str)
    booking_start_t = booking_start.astimezone(timezone.get_current_timezone()).time()

    if booking_start_t < book_start_t:
        raise ValueError(f"Bu kunda bron faqat {book_start_str} dan boshlanadi.")

    if booking_start_t >= book_end_t:
        raise ValueError(f"Bu kunda bron faqat {book_end_str} gacha qabul qilinadi.")


def validate_cleaning_time(table, booking_start, booking_end, exclude_booking_id=None):
    """
    Ketma-ket bronlar orasida 15 daqiqa tozalash vaqti bo'lishi kerak.
    """
    cleaning_time = timedelta(minutes=15)

    # Oldingi bron bilan gap
    prev_qs = Booking.objects.filter(
        table=table,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_end__lte=booking_start,
        booking_end__gt=booking_start - cleaning_time,
    )
    if exclude_booking_id:
        prev_qs = prev_qs.exclude(id=exclude_booking_id)

    if prev_qs.exists():
        prev = prev_qs.order_by("-booking_end").first()
        needed_start = prev.booking_end + cleaning_time
        raise ValueError(
            f"Stolni tozalash uchun 15 daqiqa kerak. "
            f"Oldingi bron {prev.booking_end.strftime('%H:%M')} da tugaydi. "
            f"{needed_start.strftime('%H:%M')} dan keyin vaqt tanlang."
        )

    # Keyingi bron bilan gap
    next_qs = Booking.objects.filter(
        table=table,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_start__gte=booking_end,
        booking_start__lt=booking_end + cleaning_time,
    )
    if exclude_booking_id:
        next_qs = next_qs.exclude(id=exclude_booking_id)

    if next_qs.exists():
        nxt = next_qs.order_by("booking_start").first()
        latest_end = nxt.booking_start - cleaning_time
        raise ValueError(
            f"Stolni tozalash uchun 15 daqiqa kerak. "
            f"Keyingi bron {nxt.booking_start.strftime('%H:%M')} da boshlanadi. "
            f"Bron tugash vaqtingiz {latest_end.strftime('%H:%M')} dan kech bo'lmasligi kerak."
        )


def validate_booking_time(booking_start, booking_end, branch, table):
    """Barcha vaqt qoidalarini bir joyda tekshiradi."""
    validate_basic_time(booking_start, booking_end)
    validate_min_advance(booking_start)
    validate_duration(booking_start, booking_end)
    validate_working_hours(booking_start, booking_end, branch)
    validate_booking_hours(booking_start, branch)


# ============================================================
# 4. SIG'IM VALIDATSIYASI
# ============================================================

def validate_booking_capacity(guest_count, table):
    if guest_count <= 0:
        raise ValueError("Mehmonlar soni 0 dan katta bo'lishi kerak.")
    if guest_count > table.seats:
        raise ValueError(
            f"Bu stol maksimal {table.seats} odam sig'adi. Siz {guest_count} kiritdingiz."
        )


def validate_children_count(children_count, guest_count):
    if children_count < 0:
        raise ValueError("Bolalar soni 0 dan kichik bo'lishi mumkin emas.")
    if children_count > guest_count * 3:
        raise ValueError(
            f"Bolalar soni ({children_count}) mehmonlar sonining 3 baravaridan ko'p bo'lishi mumkin emas."
        )


# ============================================================
# 5. STATUS VALIDATSIYASI
# ============================================================

_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["confirmed", "canceled"],
    "confirmed": ["checked_in", "canceled", "no_show"],
    "checked_in": ["completed", "canceled"],
    "completed": [],
    "canceled": [],
    "no_show": [],
}


def validate_status_transition(old_status: str, new_status: str):
    allowed = _ALLOWED_TRANSITIONS.get(old_status)
    if allowed is None:
        raise ValueError(f"Noto'g'ri oldingi status: '{old_status}'.")
    if new_status not in allowed:
        if allowed:
            raise ValueError(
                f"'{old_status}' dan '{new_status}' ga o'tish mumkin emas. "
                f"Ruxsat etilgan: {', '.join(allowed)}."
            )
        raise ValueError(f"'{old_status}' statusidan boshqa statusga o'tib bo'lmaydi.")


def validate_cancel_allowed(booking):
    if booking.status in ["completed", "canceled", "no_show"]:
        raise ValueError(f"'{booking.status}' statusidagi bronni bekor qilib bo'lmaydi.")

    now = timezone.now()
    minutes_until_start = (booking.booking_start - now).total_seconds() / 60
    if 0 < minutes_until_start < 15:
        raise ValueError(
            f"Bron boshlanishiga {int(minutes_until_start)} daqiqa qoldi. Bekor qilib bo'lmaydi."
        )


# ============================================================
# 6. BRON YARATISH
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
    Yangi bron yaratadi. Barcha biznes qoidalar shu yerda tekshiriladi.
    Serializer bu funksiyani chaqirishdan oldin faqat maydon formatini tekshiradi.
    """
    validate_booking_relations(branch, floor, zone, table)

    if not table.is_active:
        raise ValueError("Stol faol emas.")

    validate_booking_time(booking_start, booking_end, branch, table)
    validate_booking_capacity(guest_count, table)
    validate_children_count(children_count, guest_count)

    if not is_table_available(table, booking_start, booking_end):
        conflict = get_overlapping_bookings(table, booking_start, booking_end).first()
        if conflict:
            raise ValueError(
                f"Bu stol {conflict.booking_start.strftime('%H:%M')}–"
                f"{conflict.booking_end.strftime('%H:%M')} vaqt oralig'ida band. "
                f"Iltimos, boshqa vaqt tanlang."
            )
        raise ValueError("Bu stol shu vaqtda band.")

    validate_cleaning_time(table, booking_start, booking_end)

    # Bir foydalanuvchining bir vaqtda bir nechta bronlari
    if Booking.objects.filter(
        user=user,
        status__in=ACTIVE_BOOKING_STATUSES,
        booking_start__lt=booking_end,
        booking_end__gt=booking_start,
    ).exists():
        raise ValueError(
            "Siz shu vaqtda allaqachon faol broniga egasiz. Bir vaqtda faqat bitta bron qilish mumkin."
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

    # Bildirishnomalar
    create_notification(
        user=user,
        type=Notification.Type.BOOKING_CREATED,
        title="Bron yaratildi",
        message=f"{branch.name} da {booking_start.strftime('%d.%m.%Y %H:%M')} uchun bron yaratildi.",
        data={"booking_id": booking.id},
    )
    if hasattr(branch, "brand") and branch.brand and branch.brand.owner and branch.brand.owner != user:
        create_notification(
            user=branch.brand.owner,
            type=Notification.Type.BOOKING_CREATED,
            title="Yangi bron",
            message=f"{branch.name} da {booking_start.strftime('%d.%m.%Y %H:%M')} uchun yangi bron.",
            data={"booking_id": booking.id},
        )

    return booking


# ============================================================
# 7. BRONNI BEKOR QILISH
# ============================================================

@transaction.atomic
def cancel_booking(*, booking: Booking, changed_by, note: str = "") -> Booking:
    validate_cancel_allowed(booking)

    old_status = booking.status
    booking.status = "canceled"
    booking.save(update_fields=["status", "updated_at"])

    BookingStatusLog.objects.create(
        booking=booking,
        old_status=old_status,
        new_status="canceled",
        changed_by=changed_by,
        note=note or "Foydalanuvchi tomonidan bekor qilindi",
    )

    create_notification(
        user=booking.user,
        type=Notification.Type.BOOKING_CANCELED,
        title="Bron bekor qilindi",
        message=(
            f"Sizning broningiz bekor qilindi."
            + (f" Sabab: {note}" if note else "")
        ),
        data={"booking_id": booking.id},
    )
    return booking


# ============================================================
# 8. STATUSNI YANGILASH
# ============================================================

@transaction.atomic
def update_booking_status(
    *, booking: Booking, new_status: str, changed_by, note: str = ""
) -> Booking:
    validate_status_transition(booking.status, new_status)

    old_status = booking.status
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
            "Bron tasdiqlandi",
            f"Stol #{booking.table.name}, {booking.booking_start.strftime('%H:%M')}.",
        ),
        "checked_in": (
            Notification.Type.BOOKING_CHECKED_IN,
            "Xush kelibsiz!",
            "Broningiz faollashtirildi.",
        ),
        "completed": (
            Notification.Type.BOOKING_COMPLETED,
            "Bron yakunlandi",
            "Bizni tanlaganingiz uchun rahmat!",
        ),
        "no_show": (
            Notification.Type.BOOKING_NO_SHOW,
            "Kelmagan",
            "Siz bron vaqtida kelmadingiz. Bron yopildi.",
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
# 9. YORDAMCHI FUNKSIYALAR
# ============================================================

def get_next_available_slot(table, start_time, duration_minutes: int = 60):
    """Stolning keyingi bo'sh vaqtini topadi."""
    cleaning = timedelta(minutes=15)
    duration = timedelta(minutes=duration_minutes)

    bookings = (
        Booking.objects.filter(
            table=table,
            status__in=ACTIVE_BOOKING_STATUSES,
            booking_end__gte=start_time,
        )
        .order_by("booking_start")
    )

    candidate = start_time
    for b in bookings:
        if candidate + duration <= b.booking_start - cleaning:
            return candidate
        candidate = b.booking_end + cleaning

    return candidate


def can_extend_booking(booking: Booking, new_end) -> bool:
    if booking.status not in ["confirmed", "checked_in"]:
        raise ValueError(f"'{booking.status}' statusidagi bronni uzaytirib bo'lmaydi.")
    if new_end <= booking.booking_end:
        raise ValueError("Yangi tugash vaqti eski tugash vaqtidan keyin bo'lishi kerak.")
    if not is_table_available(booking.table, booking.booking_end, new_end, exclude_booking_id=booking.id):
        raise ValueError("Stol keyingi vaqtda band. Uzaytirib bo'lmaydi.")
    return True