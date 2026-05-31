from rest_framework import generics, permissions

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
from .permissions import IsOwnerManagerOrSuperAdmin, IsPartnerLayoutViewer


def _floor_qs_for_user(user):
    qs = Floor.objects.select_related("branch__brand").prefetch_related("zones")
    if user.role == User.Role.SUPERADMIN:
        return qs
    if user.role == User.Role.OWNER:
        return qs.filter(branch__brand__owner=user)
    # Manager / Receptionist — only their assigned branch
    return qs.filter(branch=user.branch)


# ────────────────────────────────────────────────────────────
# PUBLIC
# ────────────────────────────────────────────────────────────

class PublicBranchFloorListView(generics.ListAPIView):
    serializer_class   = FloorListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Floor.objects.none()
        return (
            Floor.objects
            .filter(branch_id=self.kwargs["branch_id"], is_active=True)
            .select_related("branch")
            .prefetch_related("zones")
        )


class PublicBranchLayoutItemsView(generics.ListAPIView):
    serializer_class   = PublicLayoutItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        branch_id = self.kwargs.get("branch_id")
        if not branch_id:
            return LayoutItem.objects.none()
        return LayoutItem.objects.filter(
            floor__branch_id=branch_id, is_active=True
        ).select_related("floor", "zone")


# ────────────────────────────────────────────────────────────
# PARTNER — floors
# ────────────────────────────────────────────────────────────

class PartnerFloorListView(generics.ListAPIView):
    serializer_class   = FloorListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerLayoutViewer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Floor.objects.none()
        return _floor_qs_for_user(self.request.user)


class PartnerFloorCreateView(generics.CreateAPIView):
    serializer_class   = FloorCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerFloorDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Floor.objects.none()
        return _floor_qs_for_user(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FloorCreateUpdateSerializer
        return FloorListSerializer


# ────────────────────────────────────────────────────────────
# PARTNER — zones
# ────────────────────────────────────────────────────────────

class PartnerZoneCreateView(generics.CreateAPIView):
    serializer_class   = ZoneCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = ZoneCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Zone.objects.none()
        user = self.request.user
        qs   = Zone.objects.select_related("floor__branch__brand")
        if user.role == User.Role.SUPERADMIN:
            return qs
        if user.role == User.Role.OWNER:
            return qs.filter(floor__branch__brand__owner=user)
        return qs.filter(floor__branch=user.branch)


# ────────────────────────────────────────────────────────────
# PARTNER — layout items
# ────────────────────────────────────────────────────────────

class PartnerLayoutItemListView(generics.ListAPIView):
    serializer_class   = LayoutItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerLayoutViewer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LayoutItem.objects.none()

        user      = self.request.user
        branch_id = self.request.query_params.get("branch_id")
        floor_id  = self.request.query_params.get("floor_id")

        qs = LayoutItem.objects.select_related("floor__branch__brand", "zone")

        if user.role == User.Role.SUPERADMIN:
            pass
        elif user.role == User.Role.OWNER:
            qs = qs.filter(floor__branch__brand__owner=user)
        else:
            qs = qs.filter(floor__branch=user.branch)

        if branch_id:
            qs = qs.filter(floor__branch_id=branch_id)
        if floor_id:
            qs = qs.filter(floor_id=floor_id)
        return qs


class PartnerLayoutItemCreateView(generics.CreateAPIView):
    serializer_class   = LayoutItemCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerLayoutItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LayoutItem.objects.none()
        user = self.request.user
        qs   = LayoutItem.objects.select_related("floor__branch__brand", "zone")
        if user.role == User.Role.SUPERADMIN:
            return qs
        if user.role == User.Role.OWNER:
            return qs.filter(floor__branch__brand__owner=user)
        return qs.filter(floor__branch=user.branch)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return LayoutItemCreateUpdateSerializer
        return LayoutItemSerializer