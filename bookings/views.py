from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from accounts.models import User
from tables.models import Table
from .models import Booking
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    ConsumerBookingCreateSerializer,
    PartnerManualBookingCreateSerializer,
    BookingCancelSerializer,
    BookingStatusUpdateSerializer,
    OccupiedTableSerializer,
)
from .permissions import IsPartnerBookingViewer, can_manage_branch_bookings
from .services import (
    cancel_booking,
    update_booking_status,
    ACTIVE_BOOKING_STATUSES,
)


# =========================
# CONSUMER
# =========================

class MyBookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
                return Booking.objects.none()
        
        return Booking.objects.filter(user=self.request.user).select_related(
            "user", "branch", "floor", "zone", "table"
        )


class MyBookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return Booking.objects.none()

        return Booking.objects.filter(user=user).select_related(
            "user", "branch", "floor", "zone", "table"
        ).prefetch_related("status_logs")


class ConsumerBookingCreateView(generics.CreateAPIView):
    serializer_class = ConsumerBookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class MyBookingCancelView(generics.GenericAPIView):
    serializer_class = BookingCancelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Booking.objects.all()

    def post(self, request, pk):
        booking = Booking.objects.filter(user=request.user, pk=pk).first()
        if not booking:
            return Response({"detail": "Booking topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cancel_booking(
                booking=booking,
                changed_by=request.user,
                note=serializer.validated_data.get("note", "")
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Booking canceled"})


# =========================
# PARTNER
# =========================

class PartnerBookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        
        user = self.request.user
        branch_id = self.request.query_params.get("branch_id")
        status_param = self.request.query_params.get("status")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        qs = Booking.objects.select_related(
            "user", "branch__brand", "floor", "zone", "table"
        )

        if user.role == User.Role.SUPERADMIN:
            pass
        elif user.role == User.Role.OWNER:
            qs = qs.filter(branch__brand__owner=user)
        else:
            qs = qs.filter(
                branch__staff_memberships__user=user,
                branch__staff_memberships__is_active=True,
            )

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
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        user = self.request.user
        qs = Booking.objects.select_related(
            "user", "branch__brand", "floor", "zone", "table"
        ).prefetch_related("status_logs")

        if user.role == User.Role.SUPERADMIN:
            return qs

        if user.role == User.Role.OWNER:
            return qs.filter(branch__brand__owner=user)

        return qs.filter(
            branch__staff_memberships__user=user,
            branch__staff_memberships__is_active=True,
        ).distinct()


class PartnerManualBookingCreateView(generics.CreateAPIView):
    serializer_class = PartnerManualBookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]


class PartnerBookingStatusUpdateView(generics.GenericAPIView):
    serializer_class = BookingStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]
    queryset = Booking.objects.all()

    def post(self, request, pk):
        booking = Booking.objects.select_related("branch__brand").filter(pk=pk).first()
        if not booking:
            return Response({"detail": "Booking topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if not can_manage_branch_bookings(request.user, booking.branch):
            return Response({"detail": "Ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            update_booking_status(
                booking=booking,
                new_status=serializer.validated_data["status"],
                changed_by=request.user,
                note=serializer.validated_data.get("note", "")
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Status updated"})


class PartnerOccupiedTablesView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]

    def get(self, request):
        branch_id = request.query_params.get("branch_id")
        floor_id = request.query_params.get("floor_id")
        zone_id = request.query_params.get("zone_id")
        booking_start = request.query_params.get("booking_start")
        booking_end = request.query_params.get("booking_end")

        if not branch_id or not booking_start or not booking_end:
            return Response(
                {"detail": "branch_id, booking_start, booking_end required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_dt = parse_datetime(booking_start)
        end_dt = parse_datetime(booking_end)

        if not start_dt or not end_dt:
            return Response({"detail": "Datetime format noto‘g‘ri"}, status=status.HTTP_400_BAD_REQUEST)

        tables_qs = Table.objects.filter(branch_id=branch_id, is_active=True).select_related("branch__brand")
        if floor_id:
            tables_qs = tables_qs.filter(floor_id=floor_id)
        if zone_id:
            tables_qs = tables_qs.filter(zone_id=zone_id)

        first_table = tables_qs.first()
        if first_table and not can_manage_branch_bookings(request.user, first_table.branch):
            return Response({"detail": "Ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        bookings_qs = Booking.objects.filter(
            table__in=tables_qs,
            status__in=ACTIVE_BOOKING_STATUSES,
            booking_start__lt=end_dt,
            booking_end__gt=start_dt,
        ).select_related("table")

        booked_map = {}
        for booking in bookings_qs:
            booked_map[booking.table_id] = booking

        data = []
        for table in tables_qs:
            active_booking = booked_map.get(table.id)
            data.append({
                "table_id": table.id,
                "is_occupied": active_booking is not None,
                "booking_id": active_booking.id if active_booking else None,
                "status": active_booking.status if active_booking else None,
            })

        return Response(data)
    


class PartnerOccupiedTablesView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPartnerBookingViewer]
    serializer_class = OccupiedTableSerializer

    def get(self, request):
        branch_id = request.query_params.get("branch_id")
        floor_id = request.query_params.get("floor_id")
        zone_id = request.query_params.get("zone_id")
        booking_start = request.query_params.get("booking_start")
        booking_end = request.query_params.get("booking_end")

        if not branch_id or not booking_start or not booking_end:
            return Response(
                {"detail": "branch_id, booking_start, booking_end required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_dt = parse_datetime(booking_start)
        end_dt = parse_datetime(booking_end)

        if not start_dt or not end_dt:
            return Response({"detail": "Datetime format noto‘g‘ri"}, status=status.HTTP_400_BAD_REQUEST)

        tables_qs = Table.objects.filter(branch_id=branch_id, is_active=True).select_related("branch__brand")
        if floor_id:
            tables_qs = tables_qs.filter(floor_id=floor_id)
        if zone_id:
            tables_qs = tables_qs.filter(zone_id=zone_id)

        first_table = tables_qs.first()
        if first_table and not can_manage_branch_bookings(request.user, first_table.branch):
            return Response({"detail": "Ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        bookings_qs = Booking.objects.filter(
            table__in=tables_qs,
            status__in=ACTIVE_BOOKING_STATUSES,
            booking_start__lt=end_dt,
            booking_end__gt=start_dt,
        ).select_related("table")

        booked_map = {}
        for booking in bookings_qs:
            booked_map[booking.table_id] = booking

        data = []
        for table in tables_qs:
            active_booking = booked_map.get(table.id)
            data.append({
                "table_id": table.id,
                "is_occupied": active_booking is not None,
                "booking_id": active_booking.id if active_booking else None,
                "status": active_booking.status if active_booking else None,
            })

        return Response(data)