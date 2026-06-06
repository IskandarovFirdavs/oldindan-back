import logging
from datetime import date as date_type

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from tables.models import Table

from .models import Booking, Message
from .permissions import IsPartnerBookingViewer, can_manage_branch_bookings
from .serializers import (
    BookingCancelSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
    BookingStatusUpdateSerializer,
    CheckInByNumberSerializer,
    ConsumerBookingCreateSerializer,
    MessageSerializer,
    PartnerManualBookingCreateSerializer,
    SendMessageSerializer,
)
from .services import (
    ACTIVE_BOOKING_STATUSES,
    cancel_booking,
    can_mark_no_show,
    checkin_by_number,
    get_slots_with_status,
    get_available_slots,
    update_booking_status,
)

logger = logging.getLogger(__name__)


# ── Pagination ───────────────────────────────────────────────

class BookingPagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = "page_size"
    max_page_size         = 100


# ── Consumer ─────────────────────────────────────────────────

class MyBookingListView(generics.ListAPIView):
    serializer_class   = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = BookingPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        qs = (
            Booking.objects.filter(user=self.request.user)
            .select_related("user", "branch", "floor", "zone", "table")
        )

        upcoming = self.request.query_params.get("upcoming")
        if upcoming == "true":
            qs = qs.filter(
                booking_start__gte=timezone.now(),
                status__in=["pending", "confirmed"],
            )
        elif self.request.query_params.get("past") == "true":
            qs = qs.filter(status__in=["completed", "canceled", "no_show"])

        return qs


class MyBookingDetailView(generics.RetrieveAPIView):
    serializer_class   = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return (
            Booking.objects.filter(user=self.request.user)
            .select_related("user", "branch", "floor", "zone", "table")
            .prefetch_related("status_logs__changed_by", "messages__sender")
        )


class ConsumerBookingCreateView(generics.CreateAPIView):
    serializer_class   = ConsumerBookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            booking = s.save()
            return Response(
                {
                    "detail": "Booking created successfully.",
                    "booking_id":     booking.id,
                    "booking_number": booking.booking_number,
                    "status":         booking.status,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("ConsumerBookingCreateView error")
            return Response(
                {"detail": "An unexpected server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MyBookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = Booking.objects.filter(user=request.user, pk=pk).first()
        if not booking:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
        s = BookingCancelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            cancel_booking(
                booking=booking,
                changed_by=request.user,
                note=s.validated_data.get("note", ""),
            )
            return Response({"detail": "Booking cancelled."})
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ── Slot grid (new — green/red availability) ─────────────────

class TableSlotsView(APIView):
    """
    GET /api/bookings/slots/
        ?table_id=4&date=2026-06-15

    Returns all 30-minute slots for the given table and date with their status:
      - available  → green
      - booked     → red
      - past       → grey (within 1-hour advance window or already past)

    Consumer-facing, no auth required.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        table_id = request.query_params.get("table_id")
        date_str = request.query_params.get("date")

        if not all([table_id, date_str]):
            return Response(
                {"detail": "table_id and date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_date = parse_date(date_str)
        if not target_date:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        table = (
            Table.objects.filter(id=table_id, is_active=True)
            .select_related("branch")
            .first()
        )
        if not table:
            return Response(
                {"detail": "Table not found or not active."},
                status=status.HTTP_404_NOT_FOUND,
            )

        slots = get_slots_with_status(
            table=table,
            branch=table.branch,
            date=target_date,
        )
        return Response({
            "date":     date_str,
            "table_id": int(table_id),
            "slots":    slots,
        })


# ── Available slots (legacy, kept for backward compat) ───────

class AvailableSlotsView(APIView):
    """
    GET /api/bookings/available-slots/
        ?branch_id=1&table_id=4&date=2026-06-15&duration=60

    Returns available start times only (no red/green grid).
    Use /api/bookings/slots/ for the full slot grid.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        branch_id  = request.query_params.get("branch_id")
        table_id   = request.query_params.get("table_id")
        date_str   = request.query_params.get("date")
        duration   = request.query_params.get("duration", 60)

        if not all([branch_id, table_id, date_str]):
            return Response(
                {"detail": "branch_id, table_id, and date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_date = parse_date(date_str)
        if not target_date:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            duration_minutes = int(duration)
            if duration_minutes < 30 or duration_minutes > 180:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"detail": "duration must be an integer between 30 and 180."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        table = (
            Table.objects.filter(id=table_id, branch_id=branch_id, is_active=True)
            .select_related("branch")
            .first()
        )
        if not table:
            return Response(
                {"detail": "Table not found or not active."},
                status=status.HTTP_404_NOT_FOUND,
            )

        slots = get_available_slots(
            table=table,
            branch=table.branch,
            date=target_date,
            duration_minutes=duration_minutes,
        )
        return Response({"date": date_str, "duration_minutes": duration_minutes, "slots": slots})


# ── Partner helpers ───────────────────────────────────────────

def _partner_booking_qs(user):
    qs = Booking.objects.select_related("user", "branch__brand", "floor", "zone", "table")
    if user.role == User.Role.SUPERADMIN:
        return qs
    if user.role == User.Role.OWNER:
        return qs.filter(branch__brand__owner=user)
    return qs.filter(branch=user.branch)


# ── Partner bookings ──────────────────────────────────────────

class PartnerBookingListView(generics.ListAPIView):
    serializer_class   = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]
    pagination_class   = BookingPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        user   = self.request.user
        params = self.request.query_params
        qs     = _partner_booking_qs(user)

        branch_id    = params.get("branch_id")
        status_param = params.get("status")
        date_from    = params.get("date_from")
        date_to      = params.get("date_to")

        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if status_param:
            qs = qs.filter(status=status_param)
        if date_from:
            qs = qs.filter(booking_start__date__gte=date_from)
        if date_to:
            qs = qs.filter(booking_start__date__lte=date_to)

        return qs.distinct()


class PartnerBookingDetailView(generics.RetrieveAPIView):
    serializer_class   = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return (
            _partner_booking_qs(self.request.user)
            .prefetch_related("status_logs__changed_by", "messages__sender")
        )


class PartnerManualBookingCreateView(generics.CreateAPIView):
    serializer_class   = PartnerManualBookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            booking = s.save()
            return Response(
                {
                    "detail": "Manual booking created.",
                    "booking_id":     booking.id,
                    "booking_number": booking.booking_number,
                    "status":         booking.status,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("PartnerManualBookingCreateView error")
            return Response(
                {"detail": "An unexpected server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PartnerBookingStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def post(self, request, pk):
        booking = (
            Booking.objects.select_related("branch__brand").filter(pk=pk).first()
        )
        if not booking:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_branch_bookings(request.user, booking.branch):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        s = BookingStatusUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            update_booking_status(
                booking=booking,
                new_status=s.validated_data["status"],
                changed_by=request.user,
                note=s.validated_data.get("note", ""),
            )
            return Response({"detail": "Status updated."})
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PartnerCheckInByNumberView(APIView):
    """
    POST /api/bookings/partner/checkin/
    Body: {"booking_number": "A3X9K2"}

    Receptionist scans/enters the booking number to check in the guest.
    Status changes from confirmed → checked_in.
    """
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def post(self, request):
        s = CheckInByNumberSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        # Determine the branch for this staff member
        user = request.user
        if user.role in [User.Role.MANAGER, User.Role.RECEPTIONIST]:
            if not user.branch:
                return Response(
                    {"detail": "Your account is not assigned to a branch."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            branch = user.branch
        else:
            # Owner/SuperAdmin — must pass branch_id
            branch_id = request.data.get("branch_id")
            if not branch_id:
                return Response(
                    {"detail": "branch_id is required for owner/admin check-in."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            from restaurants.models import Branch
            branch = Branch.objects.filter(id=branch_id).first()
            if not branch:
                return Response({"detail": "Branch not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            booking = checkin_by_number(
                booking_number=s.validated_data["booking_number"],
                branch=branch,
                changed_by=user,
            )
            return Response({
                "detail": "Guest checked in successfully.",
                "booking_id":     booking.id,
                "booking_number": booking.booking_number,
                "guest":          f"{booking.user.first_name} {booking.user.last_name}".strip() or booking.user.phone,
                "table":          booking.table.name,
            })
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PartnerMarkNoShowView(APIView):
    """
    POST /api/bookings/partner/<pk>/no-show/

    Marks a booking as no-show if the grace period has passed.
    """
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def post(self, request, pk):
        booking = (
            Booking.objects.select_related("branch__brand").filter(pk=pk).first()
        )
        if not booking:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_branch_bookings(request.user, booking.branch):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        if not can_mark_no_show(booking):
            from .services import get_no_show_grace_minutes
            grace = get_no_show_grace_minutes(booking)
            return Response(
                {
                    "detail": (
                        f"Cannot mark no-show yet. Grace period is {grace} minutes "
                        f"after booking start ({booking.booking_start.strftime('%H:%M')})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            update_booking_status(
                booking=booking,
                new_status="no_show",
                changed_by=request.user,
                note=request.data.get("note", ""),
            )
            return Response({"detail": "Booking marked as no-show."})
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PartnerOccupiedTablesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def get(self, request):
        branch_id     = request.query_params.get("branch_id")
        floor_id      = request.query_params.get("floor_id")
        zone_id       = request.query_params.get("zone_id")
        booking_start = request.query_params.get("booking_start")
        booking_end   = request.query_params.get("booking_end")

        if not all([branch_id, booking_start, booking_end]):
            return Response(
                {"detail": "branch_id, booking_start, and booking_end are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_dt = parse_datetime(booking_start)
        end_dt   = parse_datetime(booking_end)
        if not start_dt or not end_dt:
            return Response(
                {"detail": "Invalid datetime format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tables_qs = Table.objects.filter(
            branch_id=branch_id, is_active=True
        ).select_related("branch__brand")
        if floor_id:
            tables_qs = tables_qs.filter(floor_id=floor_id)
        if zone_id:
            tables_qs = tables_qs.filter(zone_id=zone_id)

        first_table = tables_qs.first()
        if first_table and not can_manage_branch_bookings(request.user, first_table.branch):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        booked_map = {
            b.table_id: b
            for b in Booking.objects.filter(
                table__in=tables_qs,
                status__in=ACTIVE_BOOKING_STATUSES,
                booking_start__lt=end_dt,
                booking_end__gt=start_dt,
            ).select_related("table")
        }

        data = [
            {
                "table_id":    t.id,
                "is_occupied": t.id in booked_map,
                "booking_id":  booked_map[t.id].id     if t.id in booked_map else None,
                "status":      booked_map[t.id].status  if t.id in booked_map else None,
            }
            for t in tables_qs
        ]
        return Response(data)


# ── Chat / Messages ───────────────────────────────────────────

class BookingMessageListView(generics.ListAPIView):
    """
    GET /api/bookings/<pk>/messages/

    Returns all messages for a booking. Accessible by:
    - The guest (booking.user)
    - Partner staff for that branch
    """
    serializer_class   = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        booking_pk = self.kwargs["pk"]
        user       = self.request.user

        # Determine access
        booking = Booking.objects.filter(pk=booking_pk).select_related("branch__brand").first()
        if not booking:
            return Message.objects.none()

        is_guest   = booking.user_id == user.id
        is_partner = can_manage_branch_bookings(user, booking.branch)
        if not is_guest and not is_partner:
            return Message.objects.none()

        # Mark messages from the other side as read
        if is_guest:
            Message.objects.filter(booking=booking, is_read=False).exclude(sender=user).update(is_read=True)
        elif is_partner:
            Message.objects.filter(booking=booking, is_read=False, sender=booking.user).update(is_read=True)

        return Message.objects.filter(booking=booking).select_related("sender")


class BookingMessageCreateView(APIView):
    """
    POST /api/bookings/<pk>/messages/
    Body: {"text": "..."}

    Send a message in a booking's chat.
    Accessible by the guest and partner staff.
    Real-time delivery via WebSocket (see chat/consumers.py).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = Booking.objects.filter(pk=pk).select_related("branch__brand", "user").first()
        if not booking:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        user       = request.user
        is_guest   = booking.user_id == user.id
        is_partner = can_manage_branch_bookings(user, booking.branch)

        if not is_guest and not is_partner:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        if booking.status in ["completed", "canceled", "no_show"]:
            return Response(
                {"detail": "Cannot send messages for a closed booking."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s = SendMessageSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        with transaction.atomic():
            message = Message.objects.create(
                booking=booking,
                sender=user,
                text=s.validated_data["text"],
            )

        # Notify recipient
        recipient = booking.branch.brand.owner if is_guest else booking.user
        if recipient and recipient != user:
            create_notification_for_message(booking, message, sender=user, recipient=recipient)

        # Broadcast via WebSocket channel layer (non-blocking)
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"booking_chat_{booking.id}",
                    {
                        "type":    "chat_message",
                        "message": MessageSerializer(message).data,
                    },
                )
        except Exception:
            pass  # WebSocket broadcast is best-effort; REST response always succeeds

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


def create_notification_for_message(booking, message, sender, recipient):
    """Send a push notification for a new chat message."""
    from notifications.services import create_notification
    from notifications.models import Notification

    sender_name = f"{sender.first_name} {sender.last_name}".strip() or sender.phone or "User"
    create_notification(
        user=recipient,
        type=Notification.Type.SYSTEM,
        title=f"New message 💬",
        message=f"{sender_name}: {message.text[:80]}",
        data={"booking_id": booking.id, "booking_number": booking.booking_number},
    )