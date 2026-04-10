from rest_framework import generics, permissions
from accounts.models import User
from .models import BranchStaff
from .serializers import (
    BranchStaffListSerializer,
    BranchStaffCreateSerializer,
    BranchStaffUpdateSerializer,
    MyStaffMembershipSerializer,
)
from .permissions import IsOwnerOrSuperAdmin


class PartnerStaffListView(generics.ListAPIView):
    serializer_class = BranchStaffListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user

        qs = BranchStaff.objects.select_related("branch__brand", "user")

        if user.role == User.Role.SUPERADMIN:
            return qs

        return qs.filter(branch__brand__owner=user)


class PartnerStaffCreateView(generics.CreateAPIView):
    serializer_class = BranchStaffCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]


class PartnerStaffDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = BranchStaffListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BranchStaff.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return BranchStaff.objects.none()

        qs = BranchStaff.objects.select_related("branch")

        if user.role == User.Role.SUPERADMIN:
            return qs

        return qs.filter(branch__brand__owner=user)


class MyStaffMembershipListView(generics.ListAPIView):
    serializer_class = MyStaffMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BranchStaff.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related("branch__brand")