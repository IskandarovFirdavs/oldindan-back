from rest_framework import serializers
from restaurants.models import Branch
from layouts.models import Floor, Zone
from tables.models import Table
from .models import Booking, BookingStatusLog
from .services import create_booking
from .permissions import can_create_manual_booking


class BookingStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingStatusLog
        fields = ["id", "old_status", "new_status", "note", "changed_by_name", "created_at"]

    def get_changed_by_name(self, obj):
        if not obj.changed_by:
            return None
        return obj.changed_by.first_name or obj.changed_by.phone or obj.changed_by.email


class BookingListSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    floor_name = serializers.CharField(source="floor.name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)
    table_name = serializers.CharField(source="table.name", read_only=True)
    user_name = serializers.SerializerMethodField()
    user_phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "user_name",
            "user_phone",
            "branch",
            "branch_name",
            "floor",
            "floor_name",
            "zone",
            "zone_name",
            "table",
            "table_name",
            "guest_count",
            "children_count",
            "booking_start",
            "booking_end",
            "status",
            "source",
            "special_request",
            "created_at",
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.phone


class BookingDetailSerializer(BookingListSerializer):
    status_logs = BookingStatusLogSerializer(many=True, read_only=True)

    class Meta(BookingListSerializer.Meta):
        fields = BookingListSerializer.Meta.fields + ["status_logs"]


class ConsumerBookingCreateSerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.filter(is_active=True))
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.filter(is_active=True))
    zone = serializers.PrimaryKeyRelatedField(queryset=Zone.objects.filter(is_active=True), required=False, allow_null=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.filter(is_active=True))
    guest_count = serializers.IntegerField(min_value=1)
    children_count = serializers.IntegerField(min_value=0, default=0)
    booking_start = serializers.DateTimeField()
    booking_end = serializers.DateTimeField()
    special_request = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        request = self.context["request"]
        return create_booking(
            user=request.user,
            branch=validated_data["branch"],
            floor=validated_data["floor"],
            zone=validated_data.get("zone"),
            table=validated_data["table"],
            guest_count=validated_data["guest_count"],
            children_count=validated_data.get("children_count", 0),
            booking_start=validated_data["booking_start"],
            booking_end=validated_data["booking_end"],
            special_request=validated_data.get("special_request", ""),
            source="app",
        )


class PartnerManualBookingCreateSerializer(serializers.Serializer):
    user = serializers.IntegerField(required=False)
    guest_name = serializers.CharField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)

    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())
    zone = serializers.PrimaryKeyRelatedField(queryset=Zone.objects.all(), required=False, allow_null=True)
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all())

    guest_count = serializers.IntegerField(min_value=1)
    children_count = serializers.IntegerField(min_value=0, default=0)
    booking_start = serializers.DateTimeField()
    booking_end = serializers.DateTimeField()
    special_request = serializers.CharField(required=False, allow_blank=True)

    def validate_branch(self, value):
        request = self.context["request"]
        if not can_create_manual_booking(request.user, value):
            raise serializers.ValidationError("Bu branch uchun manual booking yaratishga ruxsat yo'q")
        return value

    def validate(self, attrs):
        request = self.context["request"]

        if attrs.get("user"):
            from accounts.models import User
            try:
                attrs["user_obj"] = User.objects.get(id=attrs["user"])
            except User.DoesNotExist:
                raise serializers.ValidationError({"user": "User topilmadi"})
        else:
            attrs["user_obj"] = request.user

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return create_booking(
            user=validated_data["user_obj"],
            branch=validated_data["branch"],
            floor=validated_data["floor"],
            zone=validated_data.get("zone"),
            table=validated_data["table"],
            guest_count=validated_data["guest_count"],
            children_count=validated_data.get("children_count", 0),
            booking_start=validated_data["booking_start"],
            booking_end=validated_data["booking_end"],
            special_request=validated_data.get("special_request", ""),
            source="partner_manual",
            created_by_staff=request.user,
        )


class BookingCancelSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class BookingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        "pending", "confirmed", "checked_in", "completed", "canceled", "no_show"
    ])
    note = serializers.CharField(required=False, allow_blank=True)


class OccupiedTableSerializer(serializers.Serializer):
    table_id = serializers.IntegerField()
    is_occupied = serializers.BooleanField()
    booking_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField(allow_null=True)