from django.urls import path
from .views import (
    UserNotificationListView,
    UnreadCountView,
    MarkAsReadView,
    MarkAllAsReadView,
)

urlpatterns = [
    path("notifications/",                     UserNotificationListView.as_view(), name="notification-list"),
    path("notifications/unread-count/",         UnreadCountView.as_view(),          name="notification-unread-count"),
    path("notifications/mark-all-read/",        MarkAllAsReadView.as_view(),        name="notification-mark-all-read"),
    path("notifications/<int:pk>/mark-read/",   MarkAsReadView.as_view(),           name="notification-mark-read"),
]