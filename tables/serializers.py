from rest_framework import serializers
from .models import Table
from layouts.models import LayoutItem, Floor, Zone
from .permissions import can_manage_branch_tables


class TableSerializer(serializers.ModelSerializer):
    layout_item_type = serializers.CharField(source="layout_item.type", read_only=True)
    floor_name = serializers.CharField(source="floor.name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)

    class Meta:
        model = Table
        fields = [
            "id",
            "branch",
            "floor",
            "floor_name",
            "zone",
            "zone_name",
            "layout_item",
            "layout_item_type",
            "name",
            "seats",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TableCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = [
            "id",
            "branch",
            "floor",
            "zone",
            "layout_item",
            "name",
            "seats",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_branch(self, value):
        request = self.context["request"]
        if not can_manage_branch_tables(request.user, value):
            raise serializers.ValidationError("Bu branch tablelarini boshqarishga ruxsat yo'q")
        return value

    def validate_seats(self, value):
        if value <= 0:
            raise serializers.ValidationError("Seats 0 dan katta bo'lishi kerak")
        return value

    def validate(self, attrs):
        branch = attrs.get("branch") or getattr(self.instance, "branch", None)
        floor = attrs.get("floor") or getattr(self.instance, "floor", None)
        zone = attrs.get("zone") if "zone" in attrs else getattr(self.instance, "zone", None)
        layout_item = attrs.get("layout_item") or getattr(self.instance, "layout_item", None)

        if floor and branch and floor.branch_id != branch.id:
            raise serializers.ValidationError("Floor shu branchga tegishli emas")

        if zone and floor and zone.floor_id != floor.id:
            raise serializers.ValidationError("Zone shu floor ga tegishli emas")

        if layout_item:
            if layout_item.type != "table":
                raise serializers.ValidationError("Faqat type='table' bo'lgan LayoutItem table bilan bog'lanadi")

            if floor and layout_item.floor_id != floor.id:
                raise serializers.ValidationError("Layout item shu floor ga tegishli emas")

            if zone and layout_item.zone_id != zone.id:
                raise serializers.ValidationError("Layout item shu zone ga tegishli emas")

        return attrs


class PublicTableSerializer(serializers.ModelSerializer):
    floor_name = serializers.CharField(source="floor.name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)
    x = serializers.IntegerField(source="layout_item.x", read_only=True)
    y = serializers.IntegerField(source="layout_item.y", read_only=True)
    width = serializers.IntegerField(source="layout_item.width", read_only=True)
    height = serializers.IntegerField(source="layout_item.height", read_only=True)
    rotation = serializers.IntegerField(source="layout_item.rotation", read_only=True)
    shape = serializers.CharField(source="layout_item.shape", read_only=True)

    class Meta:
        model = Table
        fields = [
            "id",
            "name",
            "seats",
            "is_active",
            "floor",
            "floor_name",
            "zone",
            "zone_name",
            "x",
            "y",
            "width",
            "height",
            "rotation",
            "shape",
        ]