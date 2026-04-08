from django.conf import settings
from django.db import models


User = settings.AUTH_USER_MODEL


class RestaurantBrand(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_restaurant_brands"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="brands/logos/", null=True, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name


class Branch(models.Model):
    brand = models.ForeignKey(
        RestaurantBrand,
        on_delete=models.CASCADE,
        related_name="branches"
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField()
    address = models.CharField(max_length=500)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)

    service_fee = models.PositiveIntegerField(default=5000)
    deposit_enabled = models.BooleanField(default=False)
    deposit_amount = models.PositiveIntegerField(default=0)

    working_hours = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]
        unique_together = ("brand", "slug")

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class BranchImage(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="branches/images/")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.branch.name} image #{self.id}"