from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone=None, email=None, password=None, **extra_fields):
        if not phone and not email:
            raise ValueError("Phone yoki email bo‘lishi shart")

        if email:
            email = self.normalize_email(email)

        user = self.model(
            phone=phone,
            email=email,
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.SUPERADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not password:
            raise ValueError("Superuser uchun password shart")

        return self.create_user(phone=phone, email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CONSUMER = "consumer", "Consumer"
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        SUPERADMIN = "superadmin", "Superadmin"

    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CONSUMER)

    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone or self.email or f"User {self.pk}"


class TelegramOTP(models.Model):
    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"
        RESET_PASSWORD = "reset_password", "Reset password"

    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone} - {self.purpose}"


class UserCreationAudit(models.Model):
    """
    Kim kimni yaratganini saqlaydi.
    Superuser -> owner
    Owner -> manager
    """
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_users"
    )
    created_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_by_logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.creator_id} -> {self.created_user_id}"