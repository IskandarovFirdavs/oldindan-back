from .models import Notification


def create_notification(*, user, type, title, message, data=None):
    return Notification.objects.create(
        user=user,
        type=type,
        title=title,
        message=message,
        data=data or {}
    )