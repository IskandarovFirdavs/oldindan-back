from django.db import transaction
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size             = 30
    page_size_query_param = "page_size"
    max_page_size         = 100


class UserNotificationListView(generics.ListAPIView):
    """
    GET /api/notifications/notifications/
    GET /api/notifications/notifications/?is_read=false
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = NotificationSerializer
    pagination_class   = NotificationPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        qs = Notification.objects.filter(user=self.request.user)

        is_read = self.request.query_params.get("is_read")
        if is_read == "false":
            qs = qs.filter(is_read=False)
        elif is_read == "true":
            qs = qs.filter(is_read=True)

        return qs


class UnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    Returns {"unread_count": N}  — useful for the badge on the mobile app.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})


class MarkAsReadView(APIView):
    """
    PATCH /api/notifications/notifications/<pk>/mark-read/
    BUG FIXED: original used generics.UpdateAPIView but called get_object()
    which raised Notification.DoesNotExist without handling it — crash for
    any notification that doesn't exist or belongs to another user.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])

        return Response(
            {
                "status": "success",
                "message": "Notification marked as read.",
                "data": NotificationSerializer(notification).data,
            }
        )


class MarkAllAsReadView(APIView):
    """
    POST /api/notifications/notifications/mark-all-read/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)

        return Response(
            {
                "status": "success",
                "message": f"{updated_count} notifications marked as read.",
                "data": {"updated_count": updated_count},
            }
        )