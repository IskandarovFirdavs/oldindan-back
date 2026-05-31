import logging

from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from tables.models import Table

from .models import Booking
from .permissions import IsPartnerBookingViewer, can_manage_branch_bookings
from .serializers import (
    BookingCancelSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
    BookingStatusUpdateSerializer,
    ConsumerBookingCreateSerializer,
    PartnerManualBookingCreateSerializer,
)
from .services import ACTIVE_BOOKING_STATUSES, cancel_booking, update_booking_status

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────
# CONSUMER
# ────────────────────────────────────────────────────────────

class MyBookingListView(generics.ListAPIView):
    serializer_class   = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return (
            Booking.objects.filter(user=self.request.user)
            .select_related("user", "branch", "floor", "zone", "table")
        )


class MyBookingDetailView(generics.RetrieveAPIView):
    serializer_class   = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return (
            Booking.objects.filter(user=self.request.user)
            .select_related("user", "branch", "floor", "zone", "table")
            .prefetch_related("status_logs")
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
                {"detail": "Bron muvaffaqiyatli yaratildi.", "booking_id": booking.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("ConsumerBookingCreateView xatosi")
            return Response(
                {"detail": "Serverda kutilmagan xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MyBookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = Booking.objects.filter(user=request.user, pk=pk).first()
        if not booking:
            return Response({"detail": "Bron topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        s = BookingCancelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            cancel_booking(
                booking=booking,
                changed_by=request.user,
                note=s.validated_data.get("note", ""),
            )
            return Response({"detail": "Bron bekor qilindi."})
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ────────────────────────────────────────────────────────────
# PARTNER — helpers
# ────────────────────────────────────────────────────────────

def _partner_booking_qs(user):
    qs = Booking.objects.select_related("user", "branch__brand", "floor", "zone", "table")
    if user.role == User.Role.SUPERADMIN:
        return qs
    if user.role == User.Role.OWNER:
        return qs.filter(branch__brand__owner=user)
    # Manager / Receptionist — only their assigned branch
    return qs.filter(branch=user.branch)


# ────────────────────────────────────────────────────────────
# PARTNER — bookings
# ────────────────────────────────────────────────────────────

class PartnerBookingListView(generics.ListAPIView):
    serializer_class   = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        user   = self.request.user
        params = self.request.query_params

        qs = _partner_booking_qs(user)

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
        return _partner_booking_qs(self.request.user).prefetch_related("status_logs")


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
                {"detail": "Manual bron yaratildi.", "booking_id": booking.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("PartnerManualBookingCreateView xatosi")
            return Response(
                {"detail": "Serverda kutilmagan xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PartnerBookingStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def post(self, request, pk):
        booking = (
            Booking.objects.select_related("branch__brand").filter(pk=pk).first()
        )
        if not booking:
            return Response({"detail": "Bron topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_branch_bookings(request.user, booking.branch):
            return Response({"detail": "Ruxsat yo'q."}, status=status.HTTP_403_FORBIDDEN)

        s = BookingStatusUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            update_booking_status(
                booking=booking,
                new_status=s.validated_data["status"],
                changed_by=request.user,
                note=s.validated_data.get("note", ""),
            )
            return Response({"detail": "Status yangilandi."})
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
                {"detail": "branch_id, booking_start, booking_end majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_dt = parse_datetime(booking_start)
        end_dt   = parse_datetime(booking_end)
        if not start_dt or not end_dt:
            return Response(
                {"detail": "Noto'g'ri datetime formati."},
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
            return Response({"detail": "Ruxsat yo'q."}, status=status.HTTP_403_FORBIDDEN)

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
                "table_id":   t.id,
                "is_occupied": t.id in booked_map,
                "booking_id":  booked_map[t.id].id if t.id in booked_map else None,
                "status":      booked_map[t.id].status if t.id in booked_map else None,
            }
            for t in tables_qs
        ]
        return Response(data)