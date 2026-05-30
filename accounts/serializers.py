from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers

from .models import User, TelegramOTP, UserCreationAudit
from .services import create_otp, verify_otp
from .sms_service import send_sms_code


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


class TokenResponseSerializer(serializers.Serializer):
    """Login/register javobini dokumentatsiya qilish uchun."""
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserSerializer()


# ---------------------------------------------------------------------------
# CONSUMER — OTP request
# ---------------------------------------------------------------------------

class ConsumerRequestRegisterOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        return value

    def create(self, validated_data):
        otp = create_otp(validated_data["phone"], TelegramOTP.Purpose.REGISTER)
        send_sms_code(otp.phone, otp.code, otp.purpose)
        return otp


# ---------------------------------------------------------------------------
# CONSUMER — register
# ---------------------------------------------------------------------------

class ConsumerRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_repeat"]:
            raise serializers.ValidationError({"password_repeat": "Parollar mos emas."})

        if User.objects.filter(phone=attrs["phone"]).exists():
            raise serializers.ValidationError({"phone": "Bu telefon raqam allaqachon mavjud."})

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
        return User.objects.create_user(
            phone=validated_data["phone"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            role=User.Role.CONSUMER,
            is_phone_verified=True,
        )


# ---------------------------------------------------------------------------
# CONSUMER — login (phone + password)
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            phone=attrs["phone"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Telefon yoki parol noto'g'ri.")
        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi faol emas.")
        attrs["user"] = user
        return attrs


# ---------------------------------------------------------------------------
# CONSUMER — forgot password
# ---------------------------------------------------------------------------

class ForgotPasswordRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if not User.objects.filter(phone=value, role=User.Role.CONSUMER).exists():
            raise serializers.ValidationError("Bu raqamga tegishli foydalanuvchi topilmadi.")
        return value

    def create(self, validated_data):
        otp = create_otp(validated_data["phone"], TelegramOTP.Purpose.RESET_PASSWORD)
        send_sms_code(otp.phone, otp.code, otp.purpose)
        return otp


class ForgotPasswordConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_repeat = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_repeat"]:
            raise serializers.ValidationError({"new_password_repeat": "Parollar bir xil emas."})

        try:
            otp = verify_otp(
                phone=attrs["phone"],
                code=attrs["code"],
                purpose=TelegramOTP.Purpose.RESET_PASSWORD,
            )
        except ValueError as e:
            raise serializers.ValidationError({"code": str(e)})

        attrs["otp_obj"] = otp
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        otp = self.validated_data["otp_obj"]
        user = User.objects.get(
            phone=self.validated_data["phone"],
            role=User.Role.CONSUMER,
        )
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        # otp is already marked used inside verify_otp()
        return user


# ---------------------------------------------------------------------------
# PROFILE update
# ---------------------------------------------------------------------------

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "bio", "email", "avatar"]


# ---------------------------------------------------------------------------
# PARTNER — email/password login (owner, superadmin, or any BranchStaff)
# ---------------------------------------------------------------------------

class PartnerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from staff.models import BranchStaff

        user = User.objects.filter(email=attrs["email"]).first()
        if not user:
            raise serializers.ValidationError("Email yoki parol noto'g'ri.")
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Email yoki parol noto'g'ri.")
        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi faol emas.")

        is_partner = (
            user.role in [User.Role.OWNER, User.Role.SUPERADMIN]
            or BranchStaff.objects.filter(user=user, is_active=True).exists()
        )
        if not is_partner:
            raise serializers.ValidationError("Bu login faqat partner foydalanuvchilar uchun.")

        attrs["user"] = user
        return attrs


# ---------------------------------------------------------------------------
# SUPERADMIN — create owner
# ---------------------------------------------------------------------------

class OwnerCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request_user = self.context["request"].user
        owner = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.OWNER,
            is_active=True,
        )
        UserCreationAudit.objects.create(creator=request_user, created_user=owner)
        return owner


# ---------------------------------------------------------------------------
# OWNER / SUPERADMIN — create staff (manager, receptionist, waiter, waitress)
# ---------------------------------------------------------------------------

STAFF_ROLES = ["manager", "receptionist", "waiter", "waitress"]


class StaffCreateSerializer(serializers.Serializer):
    """
    Owner yoki Superadmin tomonidan staff (manager, receptionist, waiter,
    waitress) yaratish. Yaratilgan User CONSUMER role oladi va BranchStaff
    yozuvi orqali branchga biriktiriladi.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=STAFF_ROLES)
    branch_id = serializers.IntegerField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud.")
        return value

    def validate(self, attrs):
        from restaurants.models import Branch
        from staff.models import BranchStaff

        request_user = self.context["request"].user

        # branch mavjudligini tekshirish
        try:
            branch = Branch.objects.select_related("brand").get(id=attrs["branch_id"])
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"branch_id": "Branch topilmadi."})

        # ruxsat tekshiruvi
        if request_user.role == User.Role.SUPERADMIN:
            pass  # hamma narsaga ruxsat
        elif request_user.role == User.Role.OWNER:
            if branch.brand.owner_id != request_user.id:
                raise serializers.ValidationError({"branch_id": "Bu branch sizga tegishli emas."})
            # owner manager yarata oladi, lekin boshqa owner yarata olmaydi
        else:
            # manager — faqat o'z branchiga, manager yarata olmaydi
            if attrs["role"] == "manager":
                raise serializers.ValidationError({"role": "Manager boshqa manager yarata olmaydi."})
            if not BranchStaff.objects.filter(
                user=request_user,
                branch=branch,
                role="manager",
                is_active=True,
            ).exists():
                raise serializers.ValidationError({"branch_id": "Siz bu branchda manager emassiz."})

        attrs["_branch"] = branch
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from staff.models import BranchStaff

        request_user = self.context["request"].user
        branch = validated_data["_branch"]

        staff_user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.CONSUMER,
            is_active=True,
        )
        BranchStaff.objects.create(
            branch=branch,
            user=staff_user,
            role=validated_data["role"],
            is_active=True,
        )
        UserCreationAudit.objects.create(creator=request_user, created_user=staff_user)
        return staff_user