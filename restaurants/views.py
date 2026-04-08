from rest_framework import generics, permissions
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


# =========================
# CONSUMER API
# =========================

class PublicBranchListView(generics.ListAPIView):
    queryset = Branch.objects.filter(is_active=True).select_related("brand").prefetch_related("images")
    serializer_class = BranchListSerializer
    permission_classes = [permissions.AllowAny]


class PublicBranchDetailView(generics.RetrieveAPIView):
    queryset = Branch.objects.filter(is_active=True).select_related("brand").prefetch_related("images")
    serializer_class = BranchDetailSerializer
    permission_classes = [permissions.AllowAny]


# =========================
# PARTNER API - BRANDS
# =========================

class PartnerBrandListView(generics.ListAPIView):
    serializer_class = RestaurantBrandListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role == "superadmin":
            return RestaurantBrand.objects.all().select_related("owner")
        return RestaurantBrand.objects.filter(owner=user).select_related("owner")


class PartnerBrandCreateView(generics.CreateAPIView):
    serializer_class = RestaurantBrandCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]


# =========================
# PARTNER API - BRANCHES
# =========================

class PartnerBranchListView(generics.ListAPIView):
    serializer_class = BranchListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Branch.objects.select_related("brand").prefetch_related("images")
        if user.role == "superadmin":
            return qs
        return qs.filter(brand__owner=user)


class PartnerBranchCreateView(generics.CreateAPIView):
    serializer_class = BranchCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]


class PartnerBranchDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = BranchDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Branch.objects.select_related("brand").prefetch_related("images")
        if user.role == "superadmin":
            return qs
        return qs.filter(brand__owner=user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return BranchCreateUpdateSerializer
        return BranchDetailSerializer


class PartnerBranchImageCreateView(generics.CreateAPIView):
    serializer_class = BranchImageCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]