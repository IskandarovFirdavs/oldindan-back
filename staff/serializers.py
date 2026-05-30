from rest_framework import serializers
from accounts.models import User
from restaurants.models import Branch
from restaurants.serializers import BranchListSerializer
from .models import BranchStaff



class StaffUserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "email", "first_name", "last_name"]


class BranchStaffListSerializer(serializers.ModelSerializer):
    user = StaffUserMiniSerializer(read_only=True)
    branch = BranchListSerializer(read_only=True)

    class Meta:
        model = BranchStaff
        fields = ["id", "branch", "user", "role", "is_active", "created_at"]


class BranchStaffCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchStaff
        fields = ["id", "branch", "user", "role", "is_active"]
        read_only_fields = ["id"]

    def validate_user(self, value):
        # User allaqachon staff bo'lmasligi kerak
        if BranchStaff.objects.filter(user=value, is_active=True).exists():
            raise serializers.ValidationError("Bu user allaqachon bir filialda staff")
        return value

    def validate(self, attrs):
        request_user = self.context["request"].user
        branch = attrs["branch"]
        role = attrs["role"]

        if request_user.role == User.Role.SUPERADMIN:
            return attrs

        if request_user.role == User.Role.OWNER:
            if branch.brand.owner_id != request_user.id:
                raise serializers.ValidationError("Bu branch sizga tegishli emas")
            return attrs

        raise serializers.ValidationError("Sizda ruxsat yo'q")
    

class BranchMiniSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)

    class Meta:
        model = Branch
        fields = ["id", "name", "brand_name"]


class BranchStaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchStaff
        fields = ["role", "is_active"]

    def validate_role(self, value):
        if value not in ["manager", "receptionist", "owner"]:
            raise serializers.ValidationError("Noto'g'ri role")
        return value


class MyStaffMembershipSerializer(serializers.ModelSerializer):
    branch = BranchMiniSerializer(read_only=True)

    class Meta:
        model = BranchStaff
        fields = ["id", "branch", "role", "is_active"]

