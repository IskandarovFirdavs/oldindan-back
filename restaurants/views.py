from django.db.models import Q
from rest_framework import generics, permissions

from accounts.models import User
from .models import RestaurantBrand, Branch, BranchImage
from .serializers import (
    RestaurantBrandListSerializer,
    RestaurantBrandCreateSerializer,
    BranchListSerializer,
    BranchDetailSerializer,
    BranchCreateUpdateSerializer,
    BranchImageCreateSerializer,
)
from .permissions import IsOwnerOrSuperAdmin


# ── Public (consumer) ─────────────────────────────────────────

class PublicBranchListView(generics.ListAPIView):
    """
    Public branch list with search and location filter.

    Query params:
      ?search=kfc          — filters by branch name, brand name, or address
      ?lat=41.3&lng=69.2   — orders results by proximity (nearest first)
    """
    serializer_class   = BranchListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Branch.objects.filter(is_active=True).select_related("brand").prefetch_related("images")

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(brand__name__icontains=search)
                | Q(address__icontains=search)
            )

        # Proximity ordering — simple Euclidean distance (good enough for MVP)
        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")
        if lat and lng:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
                from django.db.models import FloatField, ExpressionWrapper, F
                from django.db.models.functions import Power, Sqrt
                qs = (
                    qs
                    .exclude(latitude__isnull=True)
                    .exclude(longitude__isnull=True)
                    .annotate(
                        distance=ExpressionWrapper(
                            Power(F("latitude") - lat_f, 2) + Power(F("longitude") - lng_f, 2),
                            output_field=FloatField(),
                        )
                    )
                    .order_by("distance")
                )
            except (ValueError, TypeError):
                pass  # Invalid coords — ignore silently

        return qs


class PublicBranchDetailView(generics.RetrieveAPIView):
    queryset           = Branch.objects.filter(is_active=True).select_related("brand").prefetch_related("images")
    serializer_class   = BranchDetailSerializer
    permission_classes = [permissions.AllowAny]


# ── Partner brands ────────────────────────────────────────────

class PartnerBrandListView(generics.ListAPIView):
    serializer_class   = RestaurantBrandListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        # FIXED: compare using User.Role enum, not raw string "superadmin"
        if user.role == User.Role.SUPERADMIN:
            return RestaurantBrand.objects.all().select_related("owner")
        return RestaurantBrand.objects.filter(owner=user).select_related("owner")


class PartnerBrandCreateView(generics.CreateAPIView):
    serializer_class   = RestaurantBrandCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]


# ── Partner branches ──────────────────────────────────────────

class PartnerBranchListView(generics.ListAPIView):
    serializer_class   = BranchListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        qs   = Branch.objects.select_related("brand").prefetch_related("images")
        # FIXED: compare using User.Role enum
        if user.role == User.Role.SUPERADMIN:
            return qs
        return qs.filter(brand__owner=user)


class PartnerBranchCreateView(generics.CreateAPIView):
    serializer_class   = BranchCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]


class PartnerBranchDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Branch.objects.none()

        user = self.request.user
        qs   = Branch.objects.select_related("brand").prefetch_related("images")

        # FIXED: compare using User.Role enum
        if user.role == User.Role.SUPERADMIN:
            return qs
        return qs.filter(brand__owner=user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return BranchCreateUpdateSerializer
        return BranchDetailSerializer


class PartnerBranchImageCreateView(generics.CreateAPIView):
    serializer_class   = BranchImageCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]