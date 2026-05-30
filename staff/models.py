from django.conf import settings
from django.db import models
from restaurants.models import Branch

User = settings.AUTH_USER_MODEL


class BranchStaff(models.Model):
    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("receptionist", "Receptionist"),
        ("waiter", "Waiter"),
        ("waitress", "Waitress"),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="staff_memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="branch_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        unique_together = ("branch", "user")

    def __str__(self):
        return f"{self.user} - {self.branch} - {self.role}"