from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers
from .models import User, TelegramOTP, UserCreationAudit
from .utils import create_otp
from .services import send_sms_code
from accounts.services import verify_otp


from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers
from .models import User, TelegramOTP, UserCreationAudit
from .utils import create_otp
from .services import send_sms_code
from accounts.services import verify_otp


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "first_name",
            "last_name",
            "bio",
            "avatar",
            "role",
            "is_phone_verified",
            "is_email_verified",
        ]
        read_only_fields = ["id", "role", "is_phone_verified", "is_email_verified"]


class ConsumerRequestRegisterOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon mavjud")
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
    password = serializers.CharField(write_only=True)
    password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_repeat"]:
            raise serializers.ValidationError({"password_repeat": "Parollar mos emas"})

        if User.objects.filter(phone=attrs["phone"]).exists():
            raise serializers.ValidationError({"phone": "Bu telefon raqam allaqachon mavjud"})

        try:
            verify_otp(
                phone=attrs["phone"],
                code=attrs["code"],
                purpose=TelegramOTP.Purpose.REGISTER,
            )
        except ValueError as e:
            raise serializers.ValidationError({"code": str(e)})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_repeat")
        validated_data.pop("code")

        user = User.objects.create_user(
            phone=validated_data["phone"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            role=User.Role.CONSUMER,
            is_phone_verified=True,
        )
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            phone=attrs["phone"],
            password=attrs["password"]
        )
        if not user:
            raise serializers.ValidationError("Telefon yoki parol noto‘g‘ri")
        if not user.is_active:
            raise serializers.ValidationError("User faol emas")
        attrs["user"] = user
        return attrs


class ForgotPasswordRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if not User.objects.filter(phone=value, role=User.Role.CONSUMER).exists():
            raise serializers.ValidationError("Consumer user topilmadi")
        return value

    def create(self, validated_data):
        otp = create_otp(validated_data["phone"], TelegramOTP.Purpose.RESET_PASSWORD)
        send_sms_code(otp.phone, otp.code, otp.purpose)
        return otp


class ForgotPasswordConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    new_password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_repeat"]:
            raise serializers.ValidationError("Parollar bir xil emas")

        otp = TelegramOTP.objects.filter(
            phone=attrs["phone"],
            code=attrs["code"],
            purpose=TelegramOTP.Purpose.RESET_PASSWORD,
            is_used=False
        ).last()

        if not otp:
            raise serializers.ValidationError("Kod noto‘g‘ri")

        if otp.is_expired():
            raise serializers.ValidationError("Kod muddati tugagan")

        attrs["otp_obj"] = otp
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        otp = self.validated_data["otp_obj"]
        user = User.objects.get(phone=self.validated_data["phone"], role=User.Role.CONSUMER)

        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "bio", "email", "avatar"]


class OwnerCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request_user = self.context["request"].user

        owner = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.OWNER,
            is_active=True
        )

        UserCreationAudit.objects.create(
            creator=request_user,
            created_user=owner
        )
        return owner


class ManagerCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request_user = self.context["request"].user

        manager = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.MANAGER,
            is_active=True
        )

        UserCreationAudit.objects.create(
            creator=request_user,
            created_user=manager
        )
        return manager


class EmailPasswordLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"]).first()

        if not user:
            raise serializers.ValidationError("Email yoki parol noto‘g‘ri")

        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Email yoki parol noto‘g‘ri")

        if not user.is_active:
            raise serializers.ValidationError("User faol emas")

        if user.role not in [User.Role.OWNER, User.Role.MANAGER, User.Role.SUPERADMIN]:
            raise serializers.ValidationError("Bu login faqat partner userlar uchun")

        attrs["user"] = user
        return attrs

class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserSerializer()


