from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.UserNotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/mark-read/', views.MarkAsReadView.as_view(), name='notification-mark-read'),
    path('notifications/mark-all-read/', views.MarkAllAsReadView.as_view(), name='notification-mark-all-read'),
]