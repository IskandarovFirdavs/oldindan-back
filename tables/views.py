from rest_framework import generics, permissions

from accounts.models import User
from .models import Table
from .serializers import TableSerializer, TableCreateUpdateSerializer, PublicTableSerializer
from .permissions import IsOwnerManagerOrSuperAdmin, IsPartnerTableViewer


def _table_qs_for_user(user):
    qs = Table.objects.select_related("branch__brand", "floor", "zone", "layout_item")
    if user.role == User.Role.SUPERADMIN:
        return qs
    if user.role == User.Role.OWNER:
        return qs.filter(branch__brand__owner=user)
    # Manager / Receptionist — only their assigned branch
    return qs.filter(branch=user.branch)


# ────────────────────────────────────────────────────────────
# PUBLIC
# ────────────────────────────────────────────────────────────

class PublicBranchTableListView(generics.ListAPIView):
    serializer_class   = PublicTableSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Table.objects.none()

        branch_id = self.kwargs["branch_id"]
        floor_id  = self.request.query_params.get("floor_id")
        zone_id   = self.request.query_params.get("zone_id")

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


# ────────────────────────────────────────────────────────────
# PARTNER
# ────────────────────────────────────────────────────────────

class PartnerTableListView(generics.ListAPIView):
    serializer_class   = TableSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartnerTableViewer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Table.objects.none()

        params    = self.request.query_params
        branch_id = params.get("branch_id")
        floor_id  = params.get("floor_id")
        zone_id   = params.get("zone_id")

        qs = _table_qs_for_user(self.request.user)

        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if floor_id:
            qs = qs.filter(floor_id=floor_id)
        if zone_id:
            qs = qs.filter(zone_id=zone_id)
        return qs


class PartnerTableCreateView(generics.CreateAPIView):
    serializer_class   = TableCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]


class PartnerTableDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerManagerOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Table.objects.none()
        return _table_qs_for_user(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return TableCreateUpdateSerializer
        return TableSerializer