from rest_framework.permissions import BasePermission
from accounts.models import User
from staff.models import BranchStaff
from restaurants.models import Branch


def can_manage_branch_tables(user, branch):
    if not user.is_authenticated:
        return False

    if user.role == User.Role.SUPERADMIN:
        return True

    if user.role == User.Role.OWNER and branch.brand.owner_id == user.id:
        return True

    return BranchStaff.objects.filter(
        user=user,
        branch=branch,
        role="manager",
        is_active=True
    ).exists()


def can_view_branch_tables(user, branch):
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
        is_active=True
    ).exists()


class IsOwnerManagerOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.OWNER,
            User.Role.MANAGER,
            User.Role.SUPERADMIN,
        ]


class IsPartnerTableViewer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.OWNER,
            User.Role.MANAGER,
            User.Role.RECEPTIONIST,
            User.Role.SUPERADMIN,
        ]