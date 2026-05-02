from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Notification
from .serializers import NotificationSerializer


class MarkAsReadView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer  # Qo'shildi
    
    def get_queryset(self):
        # drf-yasg uchun fake view
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)
    
    def get_object(self):
        # drf-yasg uchun fake view
        if getattr(self, 'swagger_fake_view', False):
            return None
        notification_id = self.kwargs.get('pk')
        return Notification.objects.get(id=notification_id, user=self.request.user)
    
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read', 'updated_at'])
        
        return Response({
            "status": "success",
            "message": "Notification marked as read",
            "data": NotificationSerializer(notification).data
        }, status=status.HTTP_200_OK)


class MarkAllAsReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer  # Qo'shildi
    
    def get_queryset(self):
        # drf-yasg uchun fake view
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user, is_read=False)
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        updated_count = self.get_queryset().update(is_read=True)
        
        return Response({
            "status": "success",
            "message": f"{updated_count} notifications marked as read",
            "data": {
                "updated_count": updated_count
            }
        }, status=status.HTTP_200_OK)


class UserNotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')