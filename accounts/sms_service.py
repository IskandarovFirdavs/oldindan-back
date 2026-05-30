"""
SMS yuborish servisi — Eskiz.uz API integratsiyasi.

Sozlamalar settings.py da:
    ESKIZ_EMAIL   = "sizning@email.com"
    ESKIZ_SECRET_KEY = "..."
    ESKIZ_FROM    = "4546"          # yoki sizning sender nomi
    ESKIZ_TEST_MODE = False          # True bo'lsa haqiqiy SMS ketmaydi
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_eskiz_token: str | None = None


def _get_eskiz_token() -> str:
    """
    Eskiz API tokenini oladi.
    Token global o'zgaruvchida keshlanadi (jarayon davomida).
    Production'da Redis yoki DB kesh ishlatish tavsiya etiladi.
    """
    global _eskiz_token
    if _eskiz_token:
        return _eskiz_token

    resp = requests.post(
        "https://notify.eskiz.uz/api/auth/login",
        data={
            "email": settings.ESKIZ_EMAIL,
            "password": settings.ESKIZ_SECRET_KEY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    _eskiz_token = resp.json()["data"]["token"]
    return _eskiz_token


def send_sms_code(phone: str, code: str, purpose: str) -> bool:
    """
    Foydalanuvchi telefoniga SMS jo'natadi.
    Muvaffaqiyatli bo'lsa True, xato bo'lsa False qaytaradi
    (va xatoni log ga yozadi — exception ko'tarmaydi,
    chunki bu OTP flow ni butunlay to'xtatmasligi kerak).
    """
    message = _build_message(code, purpose)

    if getattr(settings, "ESKIZ_TEST_MODE", False):
        logger.info("[SMS TEST] phone=%s purpose=%s code=%s", phone, purpose, code)
        return True

    try:
        token = _get_eskiz_token()
        resp = requests.post(
            "https://notify.eskiz.uz/api/message/sms/send",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "mobile_phone": _normalize_phone(phone),
                "message": message,
                "from": getattr(settings, "ESKIZ_FROM", "4546"),
                "callback_url": "",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "waiting":
            logger.warning("Eskiz noto'g'ri status qaytardi: %s", data)
            return False
        return True

    except requests.RequestException as exc:
        logger.exception("SMS yuborishda xato (phone=%s): %s", phone, exc)
        # Token muddati o'tgan bo'lishi mumkin — keshni tozalaymiz
        global _eskiz_token
        _eskiz_token = None
        return False


def _build_message(code: str, purpose: str) -> str:
    if purpose == "register":
        return f"OLDINDAN ro'yxatdan o'tish kodi: {code}. Hech kimga bermang."
    if purpose == "reset_password":
        return f"OLDINDAN parol tiklash kodi: {code}. Hech kimga bermang."
    return f"OLDINDAN tasdiqlash kodi: {code}"


def _normalize_phone(phone: str) -> str:
    """
    '+998901234567' yoki '998901234567' formatga keltiradi.
    Eskiz leading '+' siz qabul qiladi.
    """
    return phone.lstrip("+")