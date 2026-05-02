import random
from django.utils import timezone
from datetime import timedelta
from .models import TelegramOTP

def generate_otp_code():
    return str(random.randint(100000, 999999))

def create_otp(phone, purpose):
    # Eski ishlatilmagan OTP larni invalid qilish
    TelegramOTP.objects.filter(
        phone=phone,
        purpose=purpose,
        is_used=False
    ).update(is_used=True)

    otp = TelegramOTP.objects.create(
        phone=phone,
        code=generate_otp_code(),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    return otp

def verify_otp(phone, code, purpose):
    otp = TelegramOTP.objects.filter(
        phone=phone,
        purpose=purpose,
        is_used=False
    ).order_by("-id").first()

    if not otp:
        raise ValueError("OTP topilmadi")

    if otp.is_expired():
        raise ValueError("OTP muddati tugagan")

    if otp.is_blocked():
        raise ValueError("Juda ko'p urinish bo'ldi")

    if otp.code != code:
        otp.attempt_count += 1
        otp.save(update_fields=["attempt_count"])
        raise ValueError("OTP noto'g'ri")

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    return otp

