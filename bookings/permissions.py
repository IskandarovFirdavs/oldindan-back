from rest_framework.permissions import BasePermission

from accounts.models import User
from staff.models import BranchStaff


def can_manage_branch_bookings(user, branch) -> bool:
    """
    Bron statusini o'zgartira oladigan foydalanuvchi:
    superadmin, branch owneri, yoki branchda manager/receptionist sifatida biriktirilgan.
    """
    if not user.is_authenticated:
        return False
    if user.role == User.Role.SUPERADMIN:
        return True
    if user.role == User.Role.OWNER and branch.brand.owner_id == user.id:
        return True
    return BranchStaff.objects.filter(
        user=user,
        branch=branch,
        role__in=["manager", "receptionist"],
        is_active=True,
    ).exists()


def can_create_manual_booking(user, branch) -> bool:
    """Manual bron yaratish huquqi — manage bilan bir xil."""
    return can_manage_branch_bookings(user, branch)


class IsPartnerBookingViewer(BasePermission):
    """
    Bronlarni ko'ra oladigan partner:
    superadmin, owner, yoki BranchStaff da bor istalgan rol.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]:
            return True
        return BranchStaff.objects.filter(user=request.user, is_active=True).exists()