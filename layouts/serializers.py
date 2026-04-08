from rest_framework import serializers
from restaurants.models import Branch
from .models import Floor, Zone, LayoutItem
from .permissions import can_manage_branch_layout


class ZoneMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["id", "name", "color", "sort_order", "is_active"]


class LayoutItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayoutItem
        fields = [
            "id",
            "floor",
            "zone",
            "type",
            "name",
            "x",
            "y",
            "width",
            "height",
            "rotation",
            "shape",
            "z_index",
            "meta",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FloorListSerializer(serializers.ModelSerializer):
    zones = ZoneMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Floor
        fields = ["id", "branch", "name", "sort_order", "is_active", "zones"]


class FloorCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ["id", "branch", "name", "sort_order", "is_active"]
        read_only_fields = ["id"]

    def validate_branch(self, value):
        request = self.context["request"]
        if not can_manage_branch_layout(request.user, value):
            raise serializers.ValidationError("Bu branch layoutini boshqarishga ruxsat yo'q")
        return value


class ZoneCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["id", "floor", "name", "color", "sort_order", "is_active"]
        read_only_fields = ["id"]

    def validate_floor(self, value):
        request = self.context["request"]
        if not can_manage_branch_layout(request.user, value.branch):
            raise serializers.ValidationError("Bu floor ga zone qo'shishga ruxsat yo'q")
        return value


class LayoutItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayoutItem
        fields = [
            "id",
            "floor",
            "zone",
            "type",
            "name",
            "x",
            "y",
            "width",
            "height",
            "rotation",
            "shape",
            "z_index",
            "meta",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_floor(self, value):
        request = self.context["request"]
        if not can_manage_branch_layout(request.user, value.branch):
            raise serializers.ValidationError("Bu floor layoutini boshqarishga ruxsat yo'q")
        return value

    def validate(self, attrs):
        floor = attrs.get("floor") or getattr(self.instance, "floor", None)
        zone = attrs.get("zone") if "zone" in attrs else getattr(self.instance, "zone", None)

        if zone and floor and zone.floor_id != floor.id:
            raise serializers.ValidationError("Zone shu floor ga tegishli emas")
        return attrs


class PublicLayoutItemSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = LayoutItem
        fields = [
            "id",
            "floor",
            "zone",
            "zone_name",
            "type",
            "name",
            "x",
            "y",
            "width",
            "height",
            "rotation",
            "shape",
            "z_index",
            "meta",
        ]


class BranchLayoutResponseSerializer(serializers.Serializer):
    floors = FloorListSerializer(many=True)
    items = PublicLayoutItemSerializer(many=True)