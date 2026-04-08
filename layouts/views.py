from rest_framework import generics, permissions
from rest_framework.response import Response
from restaurants.models import Branch
from staff.models import BranchStaff
from accounts.models import User

from .models import Floor, Zone, LayoutItem
from .serializers import (
    FloorListSerializer,
    FloorCreateUpdateSerializer,
    ZoneCreateUpdateSerializer,
    LayoutItemSerializer,
    LayoutItemCreateUpdateSerializer,
    PublicLayoutItemSerializer,
)
from .permissions import (
    IsOwnerManagerOrSuperAdmin,
    IsPartnerLayoutViewer,
    can_manage_branch_layout,
    can_view_branch_layout,
)


# =========================
# CONSUMER PUBLIC LAYOUT
# =========================

class PublicBranchFloorListView(generics.ListAPIView):
    serializer_class = FloorListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        branch_id = self.kwargs["branch_id"]
        return Floor.objects.filter(
            branch_id=branch_id,
            is_active=True,
            branch__is_active=True
        ).prefetch_related("zones")


class PublicBranchLayoutItemsView(generics.ListAPIView):
    serializer_class = PublicLayoutItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        branch_id = self.kwargs["branch_id"]
        floor_id = self.request.query_params.get("floor_id")

        qs = LayoutItem.objects.filter(
            floor__branch_id=branch_id,
            is_active=True,
            floor__is_active=True,
            floor__branch__is_active=True
        ).select_related("floor", "zone")

        if floor_id:
            qs = qs.filter(floor_id=floor_id)

        return qs


# =========================
# PARTNER FLOOR
# =========================

class PartnerFloorListView(generics.ListAPIView):
    serializer_class = FloorListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerLayoutViewer]

    def get_queryset(self):
        user = self.request.user
        qs = Floor.objects.select_related("branch__brand").prefetch_related("zones")

        if user.role == User.Role.SUPERADMIN:
            return qs

        owner_qs = qs.filter(branch__brand__owner=user)
        staff_qs = qs.filter(
            branch__staff_memberships__user=user,
            branch__staff_memberships__is_active=True,
        )
        return (owner_qs | staff_qs).distinct()


class PartnerFloorCreateView(generics.CreateAPIView):
    serializer_class = FloorCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerFloorDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Floor.objects.select_related("branch__brand")

        if user.role == User.Role.SUPERADMIN:
            return qs

        owner_qs = qs.filter(branch__brand__owner=user)
        manager_qs = qs.filter(
            branch__staff_memberships__user=user,
            branch__staff_memberships__role="manager",
            branch__staff_memberships__is_active=True,
        )
        return (owner_qs | manager_qs).distinct()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FloorCreateUpdateSerializer
        return FloorListSerializer


# =========================
# PARTNER ZONE
# =========================

class PartnerZoneCreateView(generics.CreateAPIView):
    serializer_class = ZoneCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Zone.objects.select_related("floor__branch__brand")

        if user.role == User.Role.SUPERADMIN:
            return qs

        owner_qs = qs.filter(floor__branch__brand__owner=user)
        manager_qs = qs.filter(
            floor__branch__staff_memberships__user=user,
            floor__branch__staff_memberships__role="manager",
            floor__branch__staff_memberships__is_active=True,
        )
        return (owner_qs | manager_qs).distinct()

    def get_serializer_class(self):
        return ZoneCreateUpdateSerializer


# =========================
# PARTNER LAYOUT ITEMS
# =========================

class PartnerLayoutItemListView(generics.ListAPIView):
    serializer_class = LayoutItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerLayoutViewer]

    def get_queryset(self):
        user = self.request.user
        branch_id = self.request.query_params.get("branch_id")
        floor_id = self.request.query_params.get("floor_id")

        qs = LayoutItem.objects.select_related("floor__branch__brand", "zone")

        if user.role == User.Role.SUPERADMIN:
            pass
        elif user.role == User.Role.OWNER:
            qs = qs.filter(floor__branch__brand__owner=user)
        else:
            qs = qs.filter(
                floor__branch__staff_memberships__user=user,
                floor__branch__staff_memberships__is_active=True,
            )

        if branch_id:
            qs = qs.filter(floor__branch_id=branch_id)
        if floor_id:
            qs = qs.filter(floor_id=floor_id)

        return qs.distinct()


class PartnerLayoutItemCreateView(generics.CreateAPIView):
    serializer_class = LayoutItemCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerLayoutItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = LayoutItem.objects.select_related("floor__branch__brand", "zone")

        if user.role == User.Role.SUPERADMIN:
            return qs

        owner_qs = qs.filter(floor__branch__brand__owner=user)
        manager_qs = qs.filter(
            floor__branch__staff_memberships__user=user,
            floor__branch__staff_memberships__role="manager",
            floor__branch__staff_memberships__is_active=True,
        )
        return (owner_qs | manager_qs).distinct()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return LayoutItemCreateUpdateSerializer
        return LayoutItemSerializer