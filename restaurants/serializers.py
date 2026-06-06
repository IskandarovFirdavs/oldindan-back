from rest_framework import serializers

from accounts.models import User
from .models import RestaurantBrand, Branch, BranchImage


class BranchImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BranchImage
        fields = ["id", "image", "sort_order", "created_at"]
        read_only_fields = ["id", "created_at"]


class RestaurantBrandListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RestaurantBrand
        fields = ["id", "name", "slug", "logo", "description", "created_at"]


class RestaurantBrandCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RestaurantBrand
        fields = ["id", "name", "slug", "logo", "description"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class BranchListSerializer(serializers.ModelSerializer):
    brand_name  = serializers.CharField(source="brand.name", read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model  = Branch
        fields = [
            "id", "brand", "brand_name", "name", "slug",
            "address", "latitude", "longitude", "phone",
            "is_active", "service_fee", "deposit_enabled", "deposit_amount",
            "first_image",
        ]

    def get_first_image(self, obj):
        first = obj.images.order_by("sort_order", "id").first()
        if not first:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(first.image.url)
        return first.image.url


class BranchDetailSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    images     = BranchImageSerializer(many=True, read_only=True)

    class Meta:
        model  = Branch
        fields = [
            "id", "brand", "brand_name", "name", "slug",
            "address", "latitude", "longitude", "phone",
            "is_active", "service_fee", "deposit_enabled", "deposit_amount",
            "working_hours", "booking_hours",
            "images", "created_at", "updated_at",
        ]


class BranchCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Branch
        fields = [
            "id", "brand", "name", "slug", "address",
            "latitude", "longitude", "phone", "is_active",
            "service_fee", "deposit_enabled", "deposit_amount",
            "working_hours", "booking_hours",
        ]
        read_only_fields = ["id"]

    def validate_brand(self, value):
        user = self.context["request"].user
        # FIXED: use User.Role.SUPERADMIN instead of "superadmin" string
        if user.role == User.Role.SUPERADMIN:
            return value
        if value.owner_id != user.id:
            raise serializers.ValidationError(
                "You can only add branches to your own brand."
            )
        return value


class BranchImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BranchImage
        fields = ["id", "branch", "image", "sort_order"]
        read_only_fields = ["id"]

    def validate_branch(self, value):
        user = self.context["request"].user
        # FIXED: use User.Role.SUPERADMIN instead of "superadmin" string
        if user.role == User.Role.SUPERADMIN:
            return value
        if value.brand.owner_id != user.id:
            raise serializers.ValidationError("This branch does not belong to you.")
        return value