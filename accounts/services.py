import secrets
from datetime import timedelta

from django.utils import timezone

from .models import TelegramOTP


def generate_otp_code() -> str:
    """
    Kriptografik jihatdan xavfsiz 6 xonali OTP kodi yaratadi.
    random.randint() ishlatilmaydi — u kriptografik emas.
    """
    return str(secrets.randbelow(900_000) + 100_000)


def create_otp(phone: str, purpose: str) -> TelegramOTP:
    """
    Yangi OTP yaratadi. Avvalgi ishlatilmagan OTPlarni bekor qiladi.
    """
    TelegramOTP.objects.filter(
        phone=phone,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    return TelegramOTP.objects.create(
        phone=phone,
        code=generate_otp_code(),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5),
    )


def verify_otp(phone: str, code: str, purpose: str) -> TelegramOTP:
    """
    OTPni tekshiradi. Muvaffaqiyatli bo'lsa OTPni is_used=True qiladi.
    Muammo bo'lsa ValueError ko'taradi.
    """
    otp = (
        TelegramOTP.objects.filter(phone=phone, purpose=purpose, is_used=False)
        .order_by("-id")
        .first()
    )

    if not otp:
        raise ValueError("OTP topilmadi yoki allaqachon ishlatilgan.")

    if otp.is_expired():
        raise ValueError("OTP muddati tugagan. Yangi kod so'rang.")

    if otp.is_blocked():
        raise ValueError("Juda ko'p noto'g'ri urinish. Yangi kod so'rang.")

    if otp.code != code:
        otp.attempt_count += 1
        otp.save(update_fields=["attempt_count"])
        remaining = otp.max_attempts - otp.attempt_count
        raise ValueError(
            f"OTP noto'g'ri. {remaining} ta urinish qoldi."
            if remaining > 0
            else "OTP noto'g'ri. Urinishlar tugadi. Yangi kod so'rang."
        )

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    return otp