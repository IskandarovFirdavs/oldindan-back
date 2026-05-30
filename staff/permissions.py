from rest_framework.permissions import BasePermission
from accounts.models import User
from .models import BranchStaff


class IsOwnerOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]


class IsManagerOrOwnerOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]:
            return True
        return BranchStaff.objects.filter(
            user=request.user, role="manager", is_active=True
        ).exists()


def user_can_access_branch(user, branch):
    if not user.is_authenticated:
        return False
    if user.role == User.Role.SUPERADMIN:
        return True
    if user.role == User.Role.OWNER and branch.brand.owner_id == user.id:
        return True
    return BranchStaff.objects.filter(user=user, branch=branch, is_active=True).exists()