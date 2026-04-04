from rest_framework.permissions import BasePermission
from .models import User


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.SUPERADMIN


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.OWNER


class IsOwnerOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [User.Role.OWNER, User.Role.SUPERADMIN]