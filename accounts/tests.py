from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from accounts.models import User, TelegramOTP, UserCreationAudit
from staff.models import BranchStaff
from restaurants.models import RestaurantBrand, Branch

User = get_user_model()


class AuthTests(TestCase):
    """Authentication va user management testlari"""

    def setUp(self):
        self.client = APIClient()
        self.phone = "+998901234567"
        self.email = "test@example.com"
        self.password = "testpass123"

        # Consumer user
        self.consumer = User.objects.create_user(
            phone=self.phone,
            password=self.password,
            first_name="Test",
            last_name="User",
            role=User.Role.CONSUMER,
            is_phone_verified=True
        )

        # Owner user
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password=self.password,
            role=User.Role.OWNER,
            is_active=True
        )

        # Superadmin
        self.superadmin = User.objects.create_superuser(
            phone="+998909999999",
            email="admin@example.com",
            password=self.password
        )

        # Brand (owner ga tegishli)
        self.brand = RestaurantBrand.objects.create(
            name="Test Brand",
            owner=self.owner,
            slug="test-brand"
        )

        # Branch
        self.branch = Branch.objects.create(
            brand=self.brand,
            name="Test Branch",
            slug="test-branch",
            address="Test Address",
            is_active=True
        )

    # ============================================================
    # 1. CONSUMER REGISTRATION
    # ============================================================

    @patch('accounts.serializers.send_sms_code')
    def test_request_register_otp_success(self, mock_send_sms):
        """1. OTP yuborish - muvaffaqiyatli"""
        mock_send_sms.return_value = True
        url = "/api/accounts/consumer/request-register-otp/"
        data = {"phone": "+998901234568"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TelegramOTP.objects.count(), 1)

    def test_request_register_otp_phone_exists(self):
        """2. Mavjud telefon raqamga OTP yuborish"""
        url = "/api/accounts/consumer/request-register-otp/"
        data = {"phone": self.phone}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_success(self):
        """3. Ro'yxatdan o'tish - muvaffaqiyatli"""
        TelegramOTP.objects.create(
            phone="+998901234569",
            code="123456",
            purpose=TelegramOTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        url = "/api/accounts/consumer/register/"
        data = {
            "phone": "+998901234569",
            "code": "123456",
            "first_name": "New",
            "last_name": "User",
            "password": "newpass123",
            "password_repeat": "newpass123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)

    def test_register_password_mismatch(self):
        """4. Parollar mos kelmasligi"""
        url = "/api/accounts/consumer/register/"
        data = {
            "phone": "+998901234569",
            "code": "123456",
            "first_name": "New",
            "last_name": "User",
            "password": "pass123",
            "password_repeat": "pass456"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 2. LOGIN
    # ============================================================

    def test_consumer_login_success(self):
        """5. Consumer login - muvaffaqiyatli"""
        url = "/api/accounts/consumer/login/"
        data = {"phone": self.phone, "password": self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_consumer_login_wrong_password(self):
        """6. Noto'g'ri parol bilan login"""
        url = "/api/accounts/consumer/login/"
        data = {"phone": self.phone, "password": "wrongpass"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partner_login_owner_success(self):
        """7. Partner (owner) login - muvaffaqiyatli"""
        url = "/api/accounts/partner/login/"
        data = {"email": "owner@example.com", "password": self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_partner_login_consumer_forbidden(self):
        """8. Consumer partner login qila olmasligi"""
        url = "/api/accounts/partner/login/"
        data = {"email": self.consumer.email, "password": self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 3. FORGOT PASSWORD
    # ============================================================

    @patch('accounts.serializers.send_sms_code')
    def test_forgot_password_request_success(self, mock_send_sms):
        """9. Parolni tiklash uchun OTP yuborish"""
        mock_send_sms.return_value = True
        url = "/api/accounts/consumer/forgot-password/request/"
        data = {"phone": self.phone}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_confirm_success(self):
        """10. Parolni tiklash - muvaffaqiyatli"""
        TelegramOTP.objects.create(
            phone=self.phone,
            code="123456",
            purpose=TelegramOTP.Purpose.RESET_PASSWORD,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        url = "/api/accounts/consumer/forgot-password/confirm/"
        data = {
            "phone": self.phone,
            "code": "123456",
            "new_password": "newpass123",
            "new_password_repeat": "newpass123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_confirm_expired_code(self):
        """11. Muddati o'tgan kod bilan parol tiklash"""
        TelegramOTP.objects.create(
            phone=self.phone,
            code="123456",
            purpose=TelegramOTP.Purpose.RESET_PASSWORD,
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        url = "/api/accounts/consumer/forgot-password/confirm/"
        data = {
            "phone": self.phone,
            "code": "123456",
            "new_password": "newpass123",
            "new_password_repeat": "newpass123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 4. PROFILE
    # ============================================================

    def test_get_me(self):
        """12. O'z profilini ko'rish"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/accounts/me/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], self.phone)

    def test_update_profile(self):
        """13. Profilni yangilash"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/accounts/me/"
        data = {"first_name": "Updated", "last_name": "Name"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.consumer.refresh_from_db()
        self.assertEqual(self.consumer.first_name, "Updated")

    # ============================================================
    # 5. OWNER CREATE (Superadmin)
    # ============================================================

    def test_superadmin_create_owner(self):
        """14. Superadmin owner yaratishi"""
        self.client.force_authenticate(user=self.superadmin)
        url = "/api/accounts/partner/create-owner/"
        data = {"email": "newowner@example.com", "password": "ownerpass123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserCreationAudit.objects.filter(creator=self.superadmin).exists())

    def test_consumer_cannot_create_owner(self):
        """15. Consumer owner yarata olmasligi"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/accounts/partner/create-owner/"
        data = {"email": "newowner@example.com", "password": "pass123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ============================================================
    # 6. STAFF CREATE (Owner or Manager via accounts app)
    # ============================================================

    def test_owner_create_manager_staff(self):
        """16. Owner manager staff yaratishi"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/accounts/partner/create-staff/"
        data = {
            "email": "newmanager@example.com",
            "password": "pass123",
            "role": "manager",
            "branch_id": self.branch.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        staff = BranchStaff.objects.filter(user__email="newmanager@example.com").first()
        self.assertIsNotNone(staff)
        self.assertEqual(staff.role, "manager")

    def test_owner_create_receptionist_staff(self):
        """17. Owner receptionist staff yaratishi"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/accounts/partner/create-staff/"
        data = {
            "email": "newreceptionist@example.com",
            "password": "pass123",
            "role": "receptionist",
            "branch_id": self.branch.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_create_receptionist(self):
        """18. Manager receptionist yaratishi"""
        manager_user = User.objects.create_user(
            email="manageruser@example.com",
            password="pass123",
            role=User.Role.CONSUMER
        )
        BranchStaff.objects.create(
            branch=self.branch,
            user=manager_user,
            role="manager",
            is_active=True
        )
        self.client.force_authenticate(user=manager_user)
        url = "/api/accounts/partner/create-staff/"
        data = {
            "email": "newreceptionist2@example.com",
            "password": "pass123",
            "role": "receptionist",
            "branch_id": self.branch.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_create_manager(self):
        """19. Manager boshqa manager yarata olmasligi"""
        manager_user = User.objects.create_user(
            email="manageruser2@example.com",
            password="pass123",
            role=User.Role.CONSUMER
        )
        BranchStaff.objects.create(
            branch=self.branch,
            user=manager_user,
            role="manager",
            is_active=True
        )
        self.client.force_authenticate(user=manager_user)
        url = "/api/accounts/partner/create-staff/"
        data = {
            "email": "newmanager2@example.com",
            "password": "pass123",
            "role": "manager",
            "branch_id": self.branch.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_consumer_cannot_create_staff(self):
        """20. Consumer staff yarata olmasligi"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/accounts/partner/create-staff/"
        data = {
            "email": "staff@example.com",
            "password": "pass123",
            "role": "waiter",
            "branch_id": self.branch.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_staff_duplicate_email(self):
        """21. Mavjud email bilan staff yaratish"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/accounts/partner/create-staff/"
        data = {
            "email": "owner@example.com",
            "password": "pass123",
            "role": "waiter",
            "branch_id": self.branch.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_staff_invalid_branch(self):
        """22. O'ziga tegishli bo'lmagan branchga staff yaratish"""
        other_brand = RestaurantBrand.objects.create(
            name="Other Brand",
            owner=self.owner,
            slug="other-brand"
        )
        other_branch = Branch.objects.create(
            brand=other_brand,
            name="Other Branch",
            slug="other-branch",
            address="Other Address"
        )
        self.client.force_authenticate(user=self.owner)
        url = "/api/accounts/partner/create-staff/"
        data = {
            "email": "newstaff@example.com",
            "password": "pass123",
            "role": "waiter",
            "branch_id": other_branch.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserModelTests(TestCase):
    """User model testlari"""

    def test_user_creation_without_phone_and_email(self):
        """23. Telefon va emailsiz user yaratish mumkin emas"""
        with self.assertRaises(ValueError):
            User.objects.create_user(phone=None, email=None)

    def test_user_str_method(self):
        """24. User __str__ metodi"""
        user = User.objects.create_user(phone="+998901234567")
        self.assertEqual(str(user), "+998901234567")
        user_no_phone = User.objects.create_user(email="test@example.com")
        self.assertEqual(str(user_no_phone), "test@example.com")

    def test_superuser_creation(self):
        """25. Superuser yaratish"""
        admin = User.objects.create_superuser(phone="+998901234568", password="admin123")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, User.Role.SUPERADMIN)

    def test_is_staff_member_property(self):
        """26. is_staff_member property si to'g'ri ishlashi"""
        consumer = User.objects.create_user(phone="+998901234569")
        self.assertFalse(consumer.is_staff_member)

        brand = RestaurantBrand.objects.create(name="Brand", owner=consumer, slug="brand")
        branch = Branch.objects.create(brand=brand, name="Branch", slug="branch", address="Addr")
        staff_user = User.objects.create_user(phone="+998901234570")
        BranchStaff.objects.create(branch=branch, user=staff_user, role="waiter")
        self.assertTrue(staff_user.is_staff_member)


class OTPServiceTests(TestCase):
    """OTP servislari testlari"""

    def test_otp_expired(self):
        """27. OTP muddati tugaganligini tekshirish"""
        otp = TelegramOTP.objects.create(
            phone="+998901234569",
            code="123456",
            purpose=TelegramOTP.Purpose.REGISTER,
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertTrue(otp.is_expired())

    def test_otp_not_expired(self):
        """28. OTP muddati tugamaganligini tekshirish"""
        otp = TelegramOTP.objects.create(
            phone="+998901234569",
            code="123456",
            purpose=TelegramOTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        self.assertFalse(otp.is_expired())

    def test_otp_blocked(self):
        """29. OTP 5 marta urinishdan keyin bloklanishi"""
        otp = TelegramOTP.objects.create(
            phone="+998901234569",
            code="123456",
            purpose=TelegramOTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
            attempt_count=5,
            max_attempts=5
        )
        self.assertTrue(otp.is_blocked())

    def test_telegram_otp_str(self):
        """30. TelegramOTP __str__ metodi"""
        otp = TelegramOTP.objects.create(
            phone="+998901234569",
            code="123456",
            purpose=TelegramOTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        self.assertIn("+998901234569", str(otp))