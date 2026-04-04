import random
from datetime import timedelta
from django.utils import timezone
from .models import TelegramOTP


def generate_otp_code():
    return str(random.randint(100000, 999999))


def create_otp(phone, purpose):
    code = generate_otp_code()
    otp = TelegramOTP.objects.create(
        phone=phone,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5)
    )
    return otp