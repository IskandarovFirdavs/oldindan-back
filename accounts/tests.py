from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from accounts.models import TelegramOTP, UserCreationAudit, BranchStaff
from restaurants.models import RestaurantBrand, Branch

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.phone = "+998901234567"
        self.email = "test@example.com"
        self.password = "testpass123"

        self.consumer = User.objects.create_user(
            phone=self.phone,
            password=self.password,
            first_name="Test",
            last_name="User",
            role=User.Role.CONSUMER,
            is_phone_verified=True
        )

        self.owner = User.objects.create_user(
            email="owner@example.com",
            password=self.password,
            role=User.Role.OWNER,
            is_active=True
        )

        self.superadmin = User.objects.create_superuser(
            phone="+998909999999",
            email="admin@example.com",
            password=self.password
        )

        self.brand = RestaurantBrand.objects.create(
            name="Test Brand",
            owner=self.owner,
            slug="test-brand"
        )
        self.branch = Branch.objects.create(
            brand=self.brand,
            name="Test Branch",
            slug="test-branch",
            address="Test Address",
            is_active=True
        )

    # --- OTP & Registration ----------------------------------------------
    @patch('accounts.serializers.send_sms_code')
    def test_request_register_otp_success(self, mock_send_sms):
        mock_send_sms.return_value = True
        response = self.client.post("/api/accounts/consumer/request-register-otp/",
                                    {"phone": "+998901234568"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TelegramOTP.objects.count(), 1)

    def test_request_register_otp_phone_exists(self):
        response = self.client.post("/api/accounts/consumer/request-register-otp/",
                                    {"phone": self.phone}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_success(self):
        TelegramOTP.objects.create(
            phone="+998901234569", code="123456", purpose=TelegramOTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        data = {"phone": "+998901234569", "code": "123456", "first_name": "New",
                "last_name": "User", "password": "newpass123", "password_repeat": "newpass123"}
        response = self.client.post("/api/accounts/consumer/register/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)

    def test_register_password_mismatch(self):
        data = {"phone": "+998901234569", "code": "123456", "first_name": "New",
                "last_name": "User", "password": "pass123", "password_repeat": "pass456"}
        response = self.client.post("/api/accounts/consumer/register/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Login ----------------------------------------------------------
    def test_consumer_login_success(self):
        response = self.client.post("/api/accounts/consumer/login/",
                                    {"phone": self.phone, "password": self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_consumer_login_wrong_password(self):
        response = self.client.post("/api/accounts/consumer/login/",
                                    {"phone": self.phone, "password": "wrong"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partner_login_owner_success(self):
        response = self.client.post("/api/accounts/partner/login/",
                                    {"email": "owner@example.com", "password": self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partner_login_consumer_forbidden(self):
        response = self.client.post("/api/accounts/partner/login/",
                                    {"email": self.consumer.email, "password": self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Forgot password ------------------------------------------------
    @patch('accounts.serializers.send_sms_code')
    def test_forgot_password_request_success(self, mock_send_sms):
        mock_send_sms.return_value = True
        response = self.client.post("/api/accounts/consumer/forgot-password/request/",
                                    {"phone": self.phone}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_confirm_success(self):
        TelegramOTP.objects.create(phone=self.phone, code="123456",
                                   purpose=TelegramOTP.Purpose.RESET_PASSWORD,
                                   expires_at=timezone.now() + timedelta(minutes=5))
        data = {"phone": self.phone, "code": "123456",
                "new_password": "newpass123", "new_password_repeat": "newpass123"}
        response = self.client.post("/api/accounts/consumer/forgot-password/confirm/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_confirm_expired_code(self):
        TelegramOTP.objects.create(phone=self.phone, code="123456",
                                   purpose=TelegramOTP.Purpose.RESET_PASSWORD,
                                   expires_at=timezone.now() - timedelta(minutes=1))
        data = {"phone": self.phone, "code": "123456",
                "new_password": "newpass123", "new_password_repeat": "newpass123"}
        response = self.client.post("/api/accounts/consumer/forgot-password/confirm/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Profile --------------------------------------------------------
    def test_get_me(self):
        self.client.force_authenticate(user=self.consumer)
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], self.phone)

    def test_update_profile(self):
        self.client.force_authenticate(user=self.consumer)
        response = self.client.patch("/api/accounts/me/",
                                     {"first_name": "Updated"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.consumer.refresh_from_db()
        self.assertEqual(self.consumer.first_name, "Updated")

    # --- Owner creation (superadmin only) ------------------------------
    def test_superadmin_create_owner(self):
        self.client.force_authenticate(user=self.superadmin)
        data = {"email": "newowner@example.com", "password": "ownerpass123"}
        response = self.client.post("/api/accounts/partner/create-owner/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserCreationAudit.objects.filter(creator=self.superadmin).exists())

    def test_consumer_cannot_create_owner(self):
        self.client.force_authenticate(user=self.consumer)
        data = {"email": "newowner@example.com", "password": "pass123"}
        response = self.client.post("/api/accounts/partner/create-owner/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Staff creation (owner / manager) ------------------------------
    def test_owner_create_manager(self):
        self.client.force_authenticate(user=self.owner)
        data = {"email": "manager@test.com", "password": "pass123", "role": "manager", "branch_id": self.branch.id}
        response = self.client.post("/api/accounts/partner/create-staff/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BranchStaff.objects.filter(user__email="manager@test.com", role="manager").exists())

    def test_owner_create_receptionist(self):
        self.client.force_authenticate(user=self.owner)
        data = {"email": "reception@test.com", "password": "pass123", "role": "receptionist", "branch_id": self.branch.id}
        response = self.client.post("/api/accounts/partner/create-staff/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_create_receptionist(self):
        manager = User.objects.create_user(email="manager@branch.com", password="pass")
        BranchStaff.objects.create(branch=self.branch, user=manager, role="manager", is_active=True)
        self.client.force_authenticate(user=manager)
        data = {"email": "newreception@test.com", "password": "pass123", "role": "receptionist", "branch_id": self.branch.id}
        response = self.client.post("/api/accounts/partner/create-staff/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_create_manager(self):
        manager = User.objects.create_user(email="manager@branch.com", password="pass")
        BranchStaff.objects.create(branch=self.branch, user=manager, role="manager", is_active=True)
        self.client.force_authenticate(user=manager)
        data = {"email": "newmanager@test.com", "password": "pass123", "role": "manager", "branch_id": self.branch.id}
        response = self.client.post("/api/accounts/partner/create-staff/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_consumer_cannot_create_staff(self):
        self.client.force_authenticate(user=self.consumer)
        data = {"email": "staff@test.com", "password": "pass123", "role": "waiter", "branch_id": self.branch.id}
        response = self.client.post("/api/accounts/partner/create-staff/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_staff_duplicate_email(self):
        self.client.force_authenticate(user=self.owner)
        User.objects.create_user(email="duplicate@test.com", password="pass")
        data = {"email": "duplicate@test.com", "password": "pass123", "role": "waiter", "branch_id": self.branch.id}
        response = self.client.post("/api/accounts/partner/create-staff/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_staff_invalid_branch(self):
        self.client.force_authenticate(user=self.owner)
        data = {"email": "staff@test.com", "password": "pass123", "role": "waiter", "branch_id": 9999}
        response = self.client.post("/api/accounts/partner/create-staff/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserModelTests(TestCase):
    def test_user_creation_without_phone_and_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(phone=None, email=None)

    def test_user_str_method(self):
        user = User.objects.create_user(phone="+998901234567")
        self.assertEqual(str(user), "+998901234567")
        user2 = User.objects.create_user(email="only@email.com")
        self.assertEqual(str(user2), "only@email.com")

    def test_superuser_creation(self):
        admin = User.objects.create_superuser(phone="+998901234568", password="admin123")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, User.Role.SUPERADMIN)

    def test_is_staff_member_property(self):
        consumer = User.objects.create_user(phone="+998901234569")
        self.assertFalse(consumer.is_staff_member)
        staff_user = User.objects.create_user(phone="+998901234570")
        BranchStaff.objects.create(branch=None, user=staff_user, role="waiter")  # branch will be set later
        self.assertTrue(staff_user.is_staff_member)


class OTPServiceTests(TestCase):
    def test_otp_expired(self):
        otp = TelegramOTP.objects.create(phone="+998901234569", code="123456", purpose=TelegramOTP.Purpose.REGISTER,
                                         expires_at=timezone.now() - timedelta(minutes=1))
        self.assertTrue(otp.is_expired())

    def test_otp_not_expired(self):
        otp = TelegramOTP.objects.create(phone="+998901234569", code="123456", purpose=TelegramOTP.Purpose.REGISTER,
                                         expires_at=timezone.now() + timedelta(minutes=5))
        self.assertFalse(otp.is_expired())

    def test_otp_blocked(self):
        otp = TelegramOTP.objects.create(phone="+998901234569", code="123456", purpose=TelegramOTP.Purpose.REGISTER,
                                         expires_at=timezone.now() + timedelta(minutes=5),
                                         attempt_count=5, max_attempts=5)
        self.assertTrue(otp.is_blocked())

    def test_telegram_otp_str(self):
        otp = TelegramOTP.objects.create(phone="+998901234569", code="123456", purpose=TelegramOTP.Purpose.REGISTER,
                                         expires_at=timezone.now() + timedelta(minutes=5))
        self.assertIn("+998901234569", str(otp))