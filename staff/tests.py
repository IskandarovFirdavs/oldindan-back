from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from staff.models import BranchStaff
from restaurants.models import RestaurantBrand, Branch

User = get_user_model()


class StaffAPITests(TestCase):
    """Staff API testlari (BranchStaff CRUD, permissions, my-memberships)"""

    def setUp(self):
        self.client = APIClient()

        # Users
        self.superadmin = User.objects.create_superuser(
            phone="+998909999999",
            password="superpass123"
        )
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="ownerpass123",
            role=User.Role.OWNER
        )
        self.consumer = User.objects.create_user(
            phone="+998901234567",
            password="consumerpass123",
            role=User.Role.CONSUMER
        )

        # Brand
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

        # Manager
        self.manager_user = User.objects.create_user(
            email="manager@example.com",
            password="managerpass123",
            role=User.Role.CONSUMER
        )
        self.manager_staff = BranchStaff.objects.create(
            branch=self.branch,
            user=self.manager_user,
            role="manager",
            is_active=True
        )

        # Receptionist
        self.receptionist_user = User.objects.create_user(
            email="receptionist@example.com",
            password="receptionpass123",
            role=User.Role.CONSUMER
        )
        self.receptionist_staff = BranchStaff.objects.create(
            branch=self.branch,
            user=self.receptionist_user,
            role="receptionist",
            is_active=True
        )

        # Waiter
        self.waiter_user = User.objects.create_user(
            email="waiter@example.com",
            password="waiterpass123",
            role=User.Role.CONSUMER
        )
        self.waiter_staff = BranchStaff.objects.create(
            branch=self.branch,
            user=self.waiter_user,
            role="waiter",
            is_active=True
        )

        # Waitress
        self.waitress_user = User.objects.create_user(
            email="waitress@example.com",
            password="waitresspass123",
            role=User.Role.CONSUMER
        )
        self.waitress_staff = BranchStaff.objects.create(
            branch=self.branch,
            user=self.waitress_user,
            role="waitress",
            is_active=True
        )

    # ============================================================
    # 1. STAFF LIST
    # ============================================================

    def test_owner_can_view_all_staff(self):
        """1. Owner o'z brandidagi barcha stafflarni ko'radi"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/staff/partner/staff/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # manager, receptionist, waiter, waitress

    def test_manager_can_view_only_own_branch_staff(self):
        """2. Manager faqat o'z branchidagi stafflarni ko'radi"""
        self.client.force_authenticate(user=self.manager_user)
        url = "/api/staff/partner/staff/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_receptionist_can_view_staff(self):
        """3. Receptionist stafflarni ko'ra olmaydi (faqat o'z memberships)"""
        self.client.force_authenticate(user=self.receptionist_user)
        url = "/api/staff/partner/staff/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # 403 bo‘lishi kerak

    def test_waiter_can_view_staff(self):
        """4. Waiter stafflarni ko'ra oladi"""
        self.client.force_authenticate(user=self.waiter_user)
        url = "/api/staff/partner/staff/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superadmin_can_view_all_staff(self):
        """5. Superadmin barcha stafflarni ko'radi"""
        self.client.force_authenticate(user=self.superadmin)
        url = "/api/staff/partner/staff/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_consumer_cannot_view_staff(self):
        """6. Consumer stafflarni ko'ra olmasligi"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/staff/partner/staff/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ============================================================
    # 2. STAFF DETAIL
    # ============================================================

    def test_owner_can_view_staff_detail(self):
        """7. Owner staff detail ko'radi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/staff/partner/staff/{self.manager_staff.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "manager")

    def test_manager_can_view_staff_detail(self):
        """8. Manager staff detail ko'radi"""
        self.client.force_authenticate(user=self.manager_user)
        url = f"/api/staff/partner/staff/{self.receptionist_staff.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_receptionist_can_view_other_staff_detail(self):
        """9. Receptionist boshqa staff detail ko'ra oladi"""
        self.client.force_authenticate(user=self.receptionist_user)
        url = f"/api/staff/partner/staff/{self.waiter_staff.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_consumer_cannot_view_staff_detail(self):
        """10. Consumer staff detail ko'ra olmasligi"""
        self.client.force_authenticate(user=self.consumer)
        url = f"/api/staff/partner/staff/{self.manager_staff.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ============================================================
    # 3. STAFF UPDATE (PATCH)
    # ============================================================

    def test_owner_can_update_staff_role(self):
        """11. Owner staff rolini o'zgartirishi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/staff/partner/staff/{self.waiter_staff.id}/"
        data = {"role": "receptionist"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.waiter_staff.refresh_from_db()
        self.assertEqual(self.waiter_staff.role, "receptionist")

    def test_owner_can_update_staff_active_status(self):
        """12. Owner staffni faol/infaol qilishi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/staff/partner/staff/{self.waiter_staff.id}/"
        data = {"is_active": False}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.waiter_staff.refresh_from_db()
        self.assertFalse(self.waiter_staff.is_active)

    def test_manager_cannot_update_staff(self):
        """13. Manager staff yangilay olmasligi"""
        self.client.force_authenticate(user=self.manager_user)
        url = f"/api/staff/partner/staff/{self.waiter_staff.id}/"
        data = {"role": "receptionist"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_receptionist_cannot_update_staff(self):
        """14. Receptionist staff yangilay olmasligi"""
        self.client.force_authenticate(user=self.receptionist_user)
        url = f"/api/staff/partner/staff/{self.waiter_staff.id}/"
        data = {"role": "manager"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ============================================================
    # 4. MY MEMBERSHIPS
    # ============================================================

    def test_manager_my_memberships(self):
        """15. Manager o'z membershipsini ko'radi"""
        self.client.force_authenticate(user=self.manager_user)
        url = "/api/staff/my-memberships/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["role"], "manager")

    def test_receptionist_my_memberships(self):
        """16. Receptionist o'z membershipsini ko'radi"""
        self.client.force_authenticate(user=self.receptionist_user)
        url = "/api/staff/my-memberships/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["role"], "receptionist")

    def test_waiter_my_memberships(self):
        """17. Waiter o'z membershipsini ko'radi"""
        self.client.force_authenticate(user=self.waiter_user)
        url = "/api/staff/my-memberships/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["role"], "waiter")

    def test_consumer_my_memberships_empty(self):
        """18. Consumer memberships bo'sh"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/staff/my-memberships/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # ============================================================
    # 5. STAFF LOGIN (via accounts app - already tested, but verify)
    # ============================================================

    def test_manager_partner_login(self):
        """19. Manager partner login qila oladi (integration)"""
        url = "/api/accounts/partner/login/"
        data = {"email": "manager@example.com", "password": "managerpass123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_receptionist_partner_login(self):
        """20. Receptionist partner login qila oladi"""
        url = "/api/accounts/partner/login/"
        data = {"email": "receptionist@example.com", "password": "receptionpass123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_waiter_partner_login(self):
        """21. Waiter partner login qila oladi"""
        url = "/api/accounts/partner/login/"
        data = {"email": "waiter@example.com", "password": "waiterpass123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_waitress_partner_login(self):
        """22. Waitress partner login qila oladi"""
        url = "/api/accounts/partner/login/"
        data = {"email": "waitress@example.com", "password": "waitresspass123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BranchStaffModelTests(TestCase):
    """BranchStaff model testlari"""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="pass",
            role=User.Role.OWNER
        )
        self.brand = RestaurantBrand.objects.create(
            name="Brand",
            owner=self.owner,
            slug="brand"
        )
        self.branch = Branch.objects.create(
            brand=self.brand,
            name="Branch",
            slug="branch",
            address="Addr"
        )
        self.user = User.objects.create_user(phone="+998901234567")

    def test_branch_staff_creation(self):
        """23. BranchStaff yaratish"""
        staff = BranchStaff.objects.create(
            branch=self.branch,
            user=self.user,
            role="manager",
            is_active=True
        )
        self.assertEqual(staff.role, "manager")
        self.assertTrue(staff.is_active)

    def test_branch_staff_str(self):
        """24. BranchStaff __str__ metodi"""
        staff = BranchStaff.objects.create(
            branch=self.branch,
            user=self.user,
            role="waiter"
        )
        expected = f"{self.user} - {self.branch} - waiter"
        self.assertEqual(str(staff), expected)

    def test_unique_together_constraint(self):
        """25. Bir branchda bir user faqat bir marta bo'lishi mumkin"""
        BranchStaff.objects.create(branch=self.branch, user=self.user, role="waiter")
        with self.assertRaises(Exception):
            BranchStaff.objects.create(branch=self.branch, user=self.user, role="manager")

    def test_role_choices(self):
        """26. Role tanlovlari to'g'ri"""
        valid_roles = ["manager", "receptionist", "waiter", "waitress"]
        for role in valid_roles:
            staff = BranchStaff.objects.create(branch=self.branch, user=self.user, role=role)
            self.assertEqual(staff.role, role)
            staff.delete()

    def test_default_is_active(self):
        """27. is_active default True"""
        staff = BranchStaff.objects.create(branch=self.branch, user=self.user, role="waiter")
        self.assertTrue(staff.is_active)