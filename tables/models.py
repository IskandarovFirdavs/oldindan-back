from django.db import models
from restaurants.models import Branch
from layouts.models import Floor, Zone, LayoutItem


class Table(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="tables"
    )
    floor = models.ForeignKey(
        Floor,
        on_delete=models.CASCADE,
        related_name="tables"
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tables"
    )
    layout_item = models.OneToOneField(
        LayoutItem,
        on_delete=models.CASCADE,
        related_name="table"
    )

    name = models.CharField(max_length=50)
    seats = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        unique_together = ("branch", "name")

    def __str__(self):
        return f"{self.branch.name} - {self.name}"