from rest_framework.permissions import BasePermission
from accounts.models import User
from .models import RestaurantBrand, Branch


class IsOwnerOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.OWNER,
            User.Role.SUPERADMIN,
        ]


class IsBrandOwnerOrSuperAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if user.role == User.Role.SUPERADMIN:
            return True

        if isinstance(obj, RestaurantBrand):
            return obj.owner_id == user.id

        if isinstance(obj, Branch):
            return obj.brand.owner_id == user.id

        return False