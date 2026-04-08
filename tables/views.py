from rest_framework import generics, permissions
from accounts.models import User
from .models import Table
from .serializers import (
    TableSerializer,
    TableCreateUpdateSerializer,
    PublicTableSerializer,
)
from .permissions import (
    IsOwnerManagerOrSuperAdmin,
    IsPartnerTableViewer,
)


# =========================
# PUBLIC / CONSUMER
# =========================

class PublicBranchTableListView(generics.ListAPIView):
    serializer_class = PublicTableSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        branch_id = self.kwargs["branch_id"]
        floor_id = self.request.query_params.get("floor_id")
        zone_id = self.request.query_params.get("zone_id")

        qs = Table.objects.filter(
            branch_id=branch_id,
            is_active=True,
            branch__is_active=True,
            floor__is_active=True,
        ).select_related("branch", "floor", "zone", "layout_item")

        if floor_id:
            qs = qs.filter(floor_id=floor_id)

        if zone_id:
            qs = qs.filter(zone_id=zone_id)

        return qs


# =========================
# PARTNER
# =========================

class PartnerTableListView(generics.ListAPIView):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerTableViewer]

    def get_queryset(self):
        user = self.request.user
        branch_id = self.request.query_params.get("branch_id")
        floor_id = self.request.query_params.get("floor_id")
        zone_id = self.request.query_params.get("zone_id")

        qs = Table.objects.select_related(
            "branch__brand",
            "floor",
            "zone",
            "layout_item",
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

        if floor_id:
            qs = qs.filter(floor_id=floor_id)

        if zone_id:
            qs = qs.filter(zone_id=zone_id)

        return qs.distinct()


class PartnerTableCreateView(generics.CreateAPIView):
    serializer_class = TableCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerTableDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Table.objects.select_related(
            "branch__brand",
            "floor",
            "zone",
            "layout_item",
        )

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
            return TableCreateUpdateSerializer
        return TableSerializer