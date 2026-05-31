from rest_framework.permissions import BasePermission

from accounts.models import User


def can_manage_branch_tables(user, branch) -> bool:
    if not user.is_authenticated:
        return False
    if user.role == User.Role.SUPERADMIN:
        return True
    if user.role == User.Role.OWNER and branch.brand.owner_id == user.id:
        return True
    return (
        user.role == User.Role.MANAGER
        and user.branch_id == branch.id
    )


def can_view_branch_tables(user, branch) -> bool:
    if not user.is_authenticated:
        return False
    if user.role == User.Role.SUPERADMIN:
        return True
    if user.role == User.Role.OWNER and branch.brand.owner_id == user.id:
        return True
    return (
        user.role in [User.Role.MANAGER, User.Role.RECEPTIONIST]
        and user.branch_id == branch.id
    )


class IsOwnerManagerOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                User.Role.OWNER,
                User.Role.MANAGER,
                User.Role.SUPERADMIN,
            ]
        )


class IsPartnerTableViewer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                User.Role.OWNER,
                User.Role.MANAGER,
                User.Role.RECEPTIONIST,
                User.Role.SUPERADMIN,
            ]
        )