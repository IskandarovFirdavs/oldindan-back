from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers

from .models import User, TelegramOTP
from .services import create_otp, verify_otp
from .sms_service import send_sms_code
from restaurants.models import Branch


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "email", "first_name", "last_name", "bio", "avatar", "role", "branch",
                  "is_phone_verified", "is_email_verified"]
        read_only_fields = ["id", "role", "is_phone_verified", "is_email_verified"]


# ------------------------------
# CONSUMER
# ------------------------------
class ConsumerRequestRegisterOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone already registered.")
        return value

    def create(self, validated_data):
        otp = create_otp(validated_data["phone"], TelegramOTP.Purpose.REGISTER)
        send_sms_code(otp.phone, otp.code, otp.purpose)
        return otp


class ConsumerRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_repeat"]:
            raise serializers.ValidationError({"password_repeat": "Passwords do not match."})
        if User.objects.filter(phone=attrs["phone"]).exists():
            raise serializers.ValidationError({"phone": "Phone already exists."})
        try:
            verify_otp(attrs["phone"], attrs["code"], TelegramOTP.Purpose.REGISTER)
        except ValueError as e:
            raise serializers.ValidationError({"code": str(e)})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_repeat")
        validated_data.pop("code")
        return User.objects.create_user(
            phone=validated_data["phone"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            role=User.Role.CONSUMER,
            is_phone_verified=True,
        )


class ConsumerLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(request=self.context.get("request"), phone=attrs["phone"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid phone or password.")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive.")
        attrs["user"] = user
        return attrs


class ConsumerForgotPasswordRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if not User.objects.filter(phone=value, role=User.Role.CONSUMER).exists():
            raise serializers.ValidationError("No consumer with this phone.")
        return value

    def create(self, validated_data):
        otp = create_otp(validated_data["phone"], TelegramOTP.Purpose.RESET_PASSWORD)
        send_sms_code(otp.phone, otp.code, otp.purpose)
        return otp


class ConsumerForgotPasswordConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_repeat"]:
            raise serializers.ValidationError({"new_password_repeat": "Passwords do not match."})
        try:
            otp = verify_otp(attrs["phone"], attrs["code"], TelegramOTP.Purpose.RESET_PASSWORD)
        except ValueError as e:
            raise serializers.ValidationError({"code": str(e)})
        attrs["otp_obj"] = otp
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        otp = self.validated_data["otp_obj"]
        user = User.objects.get(phone=self.validated_data["phone"], role=User.Role.CONSUMER)
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


# ------------------------------
# OWNER (email only, no phone required)
# ------------------------------
class OwnerRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_repeat = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_repeat"]:
            raise serializers.ValidationError({"password_repeat": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_repeat")
        return User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            role=User.Role.OWNER,
            is_email_verified=True,
        )


class OwnerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"]).first()
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive.")
        if user.role != User.Role.OWNER:
            raise serializers.ValidationError("Not an owner account.")
        attrs["user"] = user
        return attrs


class OwnerForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value, role=User.Role.OWNER).exists():
            raise serializers.ValidationError("No owner with this email.")
        return value

    def create(self, validated_data):
        otp = create_otp(validated_data["email"], TelegramOTP.Purpose.RESET_PASSWORD)
        send_sms_code(otp.phone, otp.code, otp.purpose)
        return otp


class OwnerForgotPasswordConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_repeat"]:
            raise serializers.ValidationError({"new_password_repeat": "Passwords do not match."})
        try:
            otp = verify_otp(attrs["email"], attrs["code"], TelegramOTP.Purpose.RESET_PASSWORD)
        except ValueError as e:
            raise serializers.ValidationError({"code": str(e)})
        attrs["otp_obj"] = otp
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        otp = self.validated_data["otp_obj"]
        user = User.objects.get(email=self.validated_data["email"], role=User.Role.OWNER)
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


# ------------------------------
# MANAGER / RECEPTIONIST (email + branch attach)
# ------------------------------
class StaffRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.ChoiceField(choices=["manager", "receptionist"])
    branch_id = serializers.IntegerField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_repeat = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_branch_id(self, value):
        try:
            branch = Branch.objects.get(id=value)
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Branch not found.")
        return branch

    def validate(self, attrs):
        if attrs["password"] != attrs["password_repeat"]:
            raise serializers.ValidationError({"password_repeat": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_repeat")
        branch = validated_data.pop("branch_id")
        role = validated_data.pop("role")
        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            role=role,
            branch=branch,  # branch ga attach
            is_email_verified=True,
        )
        return user


class StaffLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"]).first()
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive.")
        if user.role not in [User.Role.MANAGER, User.Role.RECEPTIONIST]:
            raise serializers.ValidationError("Not a staff account.")
        if not user.branch:
            raise serializers.ValidationError("Staff not assigned to any branch.")
        attrs["user"] = user
        return attrs


class StaffForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value, role__in=[User.Role.MANAGER, User.Role.RECEPTIONIST]).exists():
            raise serializers.ValidationError("No staff with this email.")
        return value

    def create(self, validated_data):
        otp = create_otp(validated_data["email"], TelegramOTP.Purpose.RESET_PASSWORD)
        send_sms_code(otp.phone, otp.code, otp.purpose)
        return otp


class StaffForgotPasswordConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_repeat"]:
            raise serializers.ValidationError({"new_password_repeat": "Passwords do not match."})
        try:
            otp = verify_otp(attrs["email"], attrs["code"], TelegramOTP.Purpose.RESET_PASSWORD)
        except ValueError as e:
            raise serializers.ValidationError({"code": str(e)})
        attrs["otp_obj"] = otp
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        otp = self.validated_data["otp_obj"]
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


# ------------------------------
# PROFILE UPDATE
# ------------------------------
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "bio", "email", "avatar", "phone"]


# ------------------------------
# SUPERADMIN CREATE OWNER
# ------------------------------
class OwnerCreateBySuperadminSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.OWNER,
            is_active=True,
        )