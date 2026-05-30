from rest_framework.permissions import BasePermission

from .models import User


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.SUPERADMIN
        )


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.OWNER
        )


class IsOwnerOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]
        )


class IsOwnerOrManager(BasePermission):
    """Owner, Superadmin yoki BranchStaff-dagi manager."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]:
            return True
        from staff.models import BranchStaff
        return BranchStaff.objects.filter(
            user=request.user,
            role="manager",
            is_active=True,
        ).exists()


class IsStaffUser(BasePermission):
    """Owner, Superadmin yoki istalgan BranchStaff (manager, receptionist, waiter, waitress)."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]:
            return True
        from staff.models import BranchStaff
        return BranchStaff.objects.filter(user=request.user, is_active=True).exists()