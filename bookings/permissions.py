from rest_framework.permissions import BasePermission

from accounts.models import User


def _is_branch_staff(user, branch) -> bool:
    """
    Manager yoki Receptionist bo'lib, aynan shu branchga biriktirilganmi?
    """
    return (
        user.role in [User.Role.MANAGER, User.Role.RECEPTIONIST]
        and user.branch_id == branch.id
    )


def can_manage_branch_bookings(user, branch) -> bool:
    """Bron statusini o'zgartira oladi."""
    if not user.is_authenticated:
        return False
    if user.role == User.Role.SUPERADMIN:
        return True
    if user.role == User.Role.OWNER and branch.brand.owner_id == user.id:
        return True
    return _is_branch_staff(user, branch)


def can_create_manual_booking(user, branch) -> bool:
    return can_manage_branch_bookings(user, branch)


class IsPartnerBookingViewer(BasePermission):
    """Bronlarni ko'ra oladi: superadmin, owner, manager, receptionist."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]:
            return True
        return request.user.role in [User.Role.MANAGER, User.Role.RECEPTIONIST]