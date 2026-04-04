# OLDINDAN Backend

Backend for OLDINDAN booking platform.

## Tech Stack

- Django
- Django REST Framework
- PostgreSQL

## Setup

````bash
git clone https://github.com/USERNAME/oldindan_back.git
cd oldindan_back
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt



# Oldindan MVP Backend

Bu repozitoriya **Oldindan** startapi uchun minimal ishchi backend kodini o'z ichiga oladi. Backend **Django** va **Django REST Framework** (DRF) asosida yozilgan. Ushbu MVP foydalanuvchilarga kafelar/restoranlar uchun stol band qilish, adminlar esa filial, zona va stol boshqaruvi bilan shug'ullanish imkonini beradi.

## Arxitektura

- **Users** – oddiy foydalanuvchilarni ro'yxatdan o'tkazish va profilni ko'rish.
- **Restaurants** – brendlar (restaurant brands), filiallar (branches), zonalar va stollarni boshqarish. Filial xodimlari (staff) uchun maxsus ruxsatnomalar mavjud.
- **Bookings** – foydalanuvchilar uchun band qilish jarayoni va filial xodimlari uchun booking statusini boshqarish.

## O'rnatish (local development)

Python 3.10+ talab qilinadi.

```bash
# virtual muhit yaratish (ixtiyoriy)
python3 -m venv venv
source venv/bin/activate

# kerakli kutubxonalarni o'rnatish
pip install -r requirements.txt

# migratsiyalarni qo'llash
python manage.py migrate

# superuser yaratish (admin panelga kirish uchun)
python manage.py createsuperuser

# serverni ishga tushirish
python manage.py runserver
````

## Asosiy endpointlar

| Endpoint                          | Method | Tavsif                                                                                                                                           |
| --------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/api/users/register/`            | POST   | Foydalanuvchini ro'yxatdan o'tkazish. `username`, `password`, `first_name`, `last_name`, `email` parametrlari kerak. Natijada token ham qaytadi. |
| `/api/auth/login/`                | POST   | Token olish uchun login endpoint (username va password).                                                                                         |
| `/api/users/me/`                  | GET    | Tizimga kirgan foydalanuvchi profilini ko'rsatadi.                                                                                               |
| `/api/restaurants/branches/`      | GET    | Barcha filiallar ro'yxati (ochiq).                                                                                                               |
| `/api/restaurants/branches/<id>/` | GET    | Filial detali, ichidagi zonalar va stollar.                                                                                                      |
| `/api/restaurants/zones/`         | POST   | Yangi zona yaratish (filial xodimlari uchun).                                                                                                    |
| `/api/restaurants/tables/`        | POST   | Yangi stol yaratish (filial xodimlari uchun).                                                                                                    |
| `/api/bookings/`                  | GET    | Foydalanuvchi o'z bookinglarini yoki staff o'z filial bookinglarini ko'radi.                                                                     |
| `/api/bookings/`                  | POST   | Yangi booking yaratish: `branch`, `booking_time`, `num_guests`, `duration_minutes` (ixtiyoriy) va `note`.                                        |
| `/api/bookings/<id>/cancel/`      | POST   | Bookingni bekor qilish.                                                                                                                          |

Admin panelga `/admin/` orqali kirib, brendlar, filiallar, zonalar, stollar va bookinglarni ko'rish/ta'rirlash mumkin.

## Ruxsatlar

- **Foydalanuvchi**: ro'yxatdan o'tadi, tizimga kiradi va booking yaratadi/ko'radi.
- **Filial xodimi**: ma'lum filialga biriktirilgan foydalanuvchi. U zonalar va stollar yaratishi, booking statusini o'zgartirishi va filial bookinglarini ko'rishi mumkin.
- **Admin (superuser)**: barcha ma'lumotlarni yaratishi va o'zgartirishi mumkin.

## Muhim eslatmalar

1. Ushbu kod MVP uchun mo'ljallangan va barcha qoidalarni batafsil yoritmaydi. Prodyushen versiya uchun qo'shimcha xavfsizlik, ro'yxatdan o'tgan foydalanuvchilarni email/telefon bilan tasdiqlash, to'lov integratsiyasi va h.k. kabi funksiyalar kerak bo'ladi.
2. Booking algoritmi sodda: filialdagi mos bo'sh stolni topadi. Band bo'lgan stollar filtrlanadi. Kelgusida aniq stol tanlash, hold/lock mexanizmi va depozit qo'llab-quvvatlash imkoniyatlari qo'shilishi mumkin.

## Papka tuzilishi

```
oldindan_mvp/
│
├── manage.py             # Django buyruq fayli
├── oldindan/             # Loyihaning asosiy konfiguratsiyasi
│   ├── settings.py       # Django sozlamalari
│   ├── urls.py           # Loyihaning URL'lari
│   ├── wsgi.py, asgi.py  # Server konfiguratsiyalari
│   └── ...
│
├── users/                # Foydalanuvchilarga oid kod
├── restaurants/          # Brend, filial, zona, stol va staff modellari
├── bookings/             # Booking modellari va ko'rinishlari
└── requirements.txt      # Zarur kutubxonalar
```
