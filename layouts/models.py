from django.db import models
from restaurants.models import Branch


class Floor(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="floors"
    )
    name = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("branch", "name")

    def __str__(self):
        return f"{self.branch.name} - {self.name}"


class Zone(models.Model):
    floor = models.ForeignKey(
        Floor,
        on_delete=models.CASCADE,
        related_name="zones"
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("floor", "name")

    def __str__(self):
        return f"{self.floor.name} - {self.name}"


class LayoutItem(models.Model):
    TYPE_CHOICES = [
        ("table", "Table"),
        ("entrance", "Entrance"),
        ("exit", "Exit"),
        ("wc", "WC"),
        ("cashier", "Cashier"),
        ("kids_area", "Kids Area"),
        ("wall", "Wall"),
        ("divider", "Divider"),
        ("decor", "Decor"),
    ]

    SHAPE_CHOICES = [
        ("round", "Round"),
        ("rect", "Rectangle"),
        ("icon", "Icon"),
    ]

    floor = models.ForeignKey(
        Floor,
        on_delete=models.CASCADE,
        related_name="layout_items"
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="layout_items"
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=100, blank=True)

    x = models.IntegerField()
    y = models.IntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    rotation = models.IntegerField(default=0)

    shape = models.CharField(max_length=20, choices=SHAPE_CHOICES, default="rect")
    z_index = models.IntegerField(default=0)

    meta = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["z_index", "id"]

    def __str__(self):
        return f"{self.floor.name} - {self.type} - {self.id}"