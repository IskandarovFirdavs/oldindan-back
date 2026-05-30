from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from restaurants.models import RestaurantBrand, Branch
from layouts.models import Floor, Zone, LayoutItem
from staff.models import BranchStaff

User = get_user_model()


class LayoutModelsTests(TestCase):
    """Layout modellari testlari"""

    def setUp(self):
        # User
        self.owner = User.objects.create_user(
            phone="+998901234567",
            password="testpass123",
            role=User.Role.OWNER
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
        
        # Floor
        self.floor = Floor.objects.create(
            branch=self.branch,
            name="Floor 1",
            sort_order=1,
            is_active=True
        )
        
        # Zone
        self.zone = Zone.objects.create(
            floor=self.floor,
            name="Zone A",
            color="#FF0000",
            sort_order=1,
            is_active=True
        )
        
        # LayoutItem
        self.layout_item = LayoutItem.objects.create(
            floor=self.floor,
            zone=self.zone,
            type="table",
            name="Table 1",
            x=100,
            y=200,
            width=50,
            height=50,
            rotation=0,
            shape="rect",
            z_index=1,
            is_active=True
        )

    # ============================================================
    # 1. FLOOR TESTS
    # ============================================================

    def test_floor_creation(self):
        """1. Floor yaratish"""
        self.assertEqual(self.floor.name, "Floor 1")
        self.assertEqual(self.floor.branch, self.branch)
        self.assertTrue(self.floor.is_active)

    def test_floor_str(self):
        """2. Floor __str__ metodi"""
        expected = f"{self.branch.name} - Floor 1"
        self.assertEqual(str(self.floor), expected)

    def test_floor_unique_together(self):
        """3. Branchda floor nomi unique bo'lishi"""
        with self.assertRaises(Exception):
            Floor.objects.create(
                branch=self.branch,
                name="Floor 1"  # Same name
            )

    def test_floor_sort_order_default(self):
        """4. Floor sort_order default 0"""
        floor2 = Floor.objects.create(
            branch=self.branch,
            name="Floor 2"
        )
        self.assertEqual(floor2.sort_order, 0)

    # ============================================================
    # 2. ZONE TESTS
    # ============================================================

    def test_zone_creation(self):
        """5. Zone yaratish"""
        self.assertEqual(self.zone.name, "Zone A")
        self.assertEqual(self.zone.floor, self.floor)
        self.assertEqual(self.zone.color, "#FF0000")

    def test_zone_str(self):
        """6. Zone __str__ metodi"""
        expected = f"{self.floor.name} - Zone A"
        self.assertEqual(str(self.zone), expected)

    def test_zone_unique_together(self):
        """7. Floorda zone nomi unique bo'lishi"""
        with self.assertRaises(Exception):
            Zone.objects.create(
                floor=self.floor,
                name="Zone A"  # Same name
            )

    def test_zone_color_blank(self):
        """8. Zone color blank bo'lishi mumkin"""
        zone2 = Zone.objects.create(
            floor=self.floor,
            name="Zone B",
            color=""
        )
        self.assertEqual(zone2.color, "")

    # ============================================================
    # 3. LAYOUT ITEM TESTS
    # ============================================================

    def test_layout_item_creation(self):
        """9. LayoutItem yaratish"""
        self.assertEqual(self.layout_item.type, "table")
        self.assertEqual(self.layout_item.x, 100)
        self.assertEqual(self.layout_item.y, 200)
        self.assertEqual(self.layout_item.width, 50)

    def test_layout_item_str(self):
        """10. LayoutItem __str__ metodi"""
        expected = f"{self.floor.name} - table - {self.layout_item.id}"
        self.assertEqual(str(self.layout_item), expected)

    def test_layout_item_shape_choices(self):
        """11. LayoutItem shape tanlovlari"""
        valid_shapes = ["round", "rect", "icon"]
        self.assertIn(self.layout_item.shape, valid_shapes)

    def test_layout_item_type_choices(self):
        """12. LayoutItem type tanlovlari"""
        valid_types = ["table", "entrance", "exit", "wc", "cashier", "kids_area", "wall", "divider", "decor"]
        self.assertIn(self.layout_item.type, valid_types)

    def test_layout_item_zone_nullable(self):
        """13. LayoutItem zone nullable"""
        item_without_zone = LayoutItem.objects.create(
            floor=self.floor,
            zone=None,
            type="wall",
            x=0, y=0, width=10, height=10
        )
        self.assertIsNone(item_without_zone.zone)


class PublicLayoutAPITests(TestCase):
    """Consumer (public) layout API testlari"""

    def setUp(self):
        self.client = APIClient()
        
        # Owner
        self.owner = User.objects.create_user(
            phone="+998901234567",
            password="testpass123",
            role=User.Role.OWNER
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
        
        # Floor
        self.floor = Floor.objects.create(
            branch=self.branch,
            name="Floor 1",
            is_active=True
        )
        
        # Zone
        self.zone = Zone.objects.create(
            floor=self.floor,
            name="Zone A",
            is_active=True
        )
        
        # Layout items
        self.layout_item = LayoutItem.objects.create(
            floor=self.floor,
            zone=self.zone,
            type="table",
            name="Table 1",
            x=100, y=200, width=50, height=50,
            is_active=True
        )
        
        self.wall_item = LayoutItem.objects.create(
            floor=self.floor,
            zone=None,
            type="wall",
            x=0, y=0, width=10, height=10,
            is_active=True
        )

    def test_public_floors_list(self):
        """14. Consumer floor list API"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/branches/{self.branch.id}/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_public_floors_unauthenticated(self):
        """15. Authentifikatsiyasiz floor list"""
        url = f"/api/layouts/branches/{self.branch.id}/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_layout_items_list(self):
        """16. Consumer layout items API"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/branches/{self.branch.id}/layout-items/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Serializer PublicLayoutItemSerializer ishlatilganligini tekshirish
        first_item = response.data[0]
        self.assertIn("zone_name", first_item)

    def test_public_layout_items_only_active(self):
        """17. Consumer faqat active layout items ko'rishi"""
        # Inactive item yaratish
        inactive_item = LayoutItem.objects.create(
            floor=self.floor,
            zone=self.zone,
            type="decor",
            x=300, y=300, width=20, height=20,
            is_active=False
        )
        
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/branches/{self.branch.id}/layout-items/"
        response = self.client.get(url)
        
        # Inactive item response da bo'lmasligi kerak
        item_ids = [item["id"] for item in response.data]
        self.assertNotIn(inactive_item.id, item_ids)


class PartnerLayoutAPITests(TestCase):
    """Partner layout API testlari"""

    def setUp(self):
        self.client = APIClient()
        
        # Users
        self.superadmin = User.objects.create_superuser(
            phone="+998909999999",
            password="superpass123"
        )
        
        self.owner = User.objects.create_user(
            phone="+998901234567",
            password="ownerpass123",
            role=User.Role.OWNER
        )
        
        self.manager = User.objects.create_user(
            phone="+998901234568",
            password="managerpass123",
            role=User.Role.MANAGER
        )
        
        self.receptionist = User.objects.create_user(
            phone="+998901234569",
            password="receptionpass123",
            role=User.Role.RECEPTIONIST
        )
        
        self.consumer = User.objects.create_user(
            phone="+998901234570",
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
        
        # Staff assignments
        BranchStaff.objects.create(
            branch=self.branch,
            user=self.manager,
            role="manager",
            is_active=True
        )
        
        BranchStaff.objects.create(
            branch=self.branch,
            user=self.receptionist,
            role="receptionist",
            is_active=True
        )
        
        # Floors
        self.floor = Floor.objects.create(
            branch=self.branch,
            name="Floor 1",
            sort_order=1,
            is_active=True
        )
        
        self.floor2 = Floor.objects.create(
            branch=self.branch,
            name="Floor 2",
            sort_order=2,
            is_active=True
        )
        
        # Zones
        self.zone = Zone.objects.create(
            floor=self.floor,
            name="Zone A",
            color="#FF0000",
            sort_order=1,
            is_active=True
        )
        
        # Layout items
        self.layout_item = LayoutItem.objects.create(
            floor=self.floor,
            zone=self.zone,
            type="table",
            name="Table 1",
            x=100, y=200, width=50, height=50,
            is_active=True
        )

    # ============================================================
    # 4. FLOOR API (Partner)
    # ============================================================

    def test_partner_floors_list_owner(self):
        """18. Owner floor list API"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/layouts/partner/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_partner_floors_list_manager(self):
        """19. Manager floor list API"""
        self.client.force_authenticate(user=self.manager)
        url = "/api/layouts/partner/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partner_floors_list_receptionist(self):
        """20. Receptionist floor list API"""
        self.client.force_authenticate(user=self.receptionist)
        url = "/api/layouts/partner/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partner_floors_list_consumer_forbidden(self):
        """21. Consumer floor list ko'ra olmasligi"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/layouts/partner/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partner_floor_create_owner(self):
        """22. Owner floor yaratishi"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/layouts/partner/floors/create/"
        data = {
            "branch": self.branch.id,
            "name": "New Floor",
            "sort_order": 3,
            "is_active": True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Floor.objects.count(), 3)

    def test_partner_floor_create_manager(self):
        """23. Manager floor yaratishi"""
        self.client.force_authenticate(user=self.manager)
        url = "/api/layouts/partner/floors/create/"
        data = {
            "branch": self.branch.id,
            "name": "Manager Floor",
            "sort_order": 3
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_partner_floor_create_consumer_forbidden(self):
        """24. Consumer floor yarata olmasligi"""
        self.client.force_authenticate(user=self.consumer)
        url = "/api/layouts/partner/floors/create/"
        data = {
            "branch": self.branch.id,
            "name": "New Floor"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partner_floor_update_owner(self):
        """25. Owner floor yangilashi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/partner/floors/{self.floor.id}/"
        data = {"name": "Updated Floor Name"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.floor.refresh_from_db()
        self.assertEqual(self.floor.name, "Updated Floor Name")

    def test_partner_floor_delete_owner(self):
        """26. Owner floor o'chirishi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/partner/floors/{self.floor2.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Floor.objects.filter(id=self.floor2.id).exists())

    # ============================================================
    # 5. ZONE API (Partner)
    # ============================================================

    def test_partner_zone_create_owner(self):
        """27. Owner zone yaratishi"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/layouts/partner/zones/create/"
        data = {
            "floor": self.floor.id,
            "name": "New Zone",
            "color": "#00FF00",
            "sort_order": 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Zone.objects.count(), 2)

    def test_partner_zone_create_invalid_floor(self):
        """28. Boshqa branddagi floor ga zone yaratish"""
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
        other_floor = Floor.objects.create(
            branch=other_branch,
            name="Other Floor"
        )
        
        self.client.force_authenticate(user=self.owner)
        url = "/api/layouts/partner/zones/create/"
        data = {
            "floor": other_floor.id,
            "name": "Invalid Zone"
        }
        response = self.client.post(url, data, format='json')
        # Owner o'ziga tegishli bo'lmagan floor ga zone yarata olmasligi kerak
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partner_zone_update_owner(self):
        """29. Owner zone yangilashi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/partner/zones/{self.zone.id}/"
        data = {"name": "Updated Zone", "color": "#0000FF"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.name, "Updated Zone")

    # ============================================================
    # 6. LAYOUT ITEM API (Partner)
    # ============================================================

    def test_partner_layout_items_list_owner(self):
        """30. Owner layout items list API"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/partner/layout-items/?branch_id={self.branch.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_partner_layout_items_list_filter_by_floor(self):
        """31. Layout items floor bo'yicha filter"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/partner/layout-items/?branch_id={self.branch.id}&floor_id={self.floor.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for item in response.data:
            self.assertEqual(item["floor"], self.floor.id)

    def test_partner_layout_item_create_owner(self):
        """32. Owner layout item yaratishi"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/layouts/partner/layout-items/create/"
        data = {
            "floor": self.floor.id,
            "zone": self.zone.id,
            "type": "wc",
            "name": "WC 1",
            "x": 200,
            "y": 300,
            "width": 40,
            "height": 40,
            "rotation": 0,
            "shape": "rect",
            "z_index": 5,
            "is_active": True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LayoutItem.objects.count(), 2)

    def test_partner_layout_item_create_without_zone(self):
        """33. Layout item zonasiz yaratish"""
        self.client.force_authenticate(user=self.owner)
        url = "/api/layouts/partner/layout-items/create/"
        data = {
            "floor": self.floor.id,
            "zone": None,
            "type": "wall",
            "name": "Wall 1",
            "x": 10,
            "y": 10,
            "width": 100,
            "height": 10
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_partner_layout_item_create_invalid_zone(self):
        """34. Boshqa floor ga tegishli zone bilan layout item yaratish"""
        other_floor = Floor.objects.create(
            branch=self.branch,
            name="Other Floor"
        )
        other_zone = Zone.objects.create(
            floor=other_floor,
            name="Other Zone"
        )
        
        self.client.force_authenticate(user=self.owner)
        url = "/api/layouts/partner/layout-items/create/"
        data = {
            "floor": self.floor.id,
            "zone": other_zone.id,
            "type": "decor",
            "x": 0, "y": 0, "width": 10, "height": 10
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partner_layout_item_update_owner(self):
        """35. Owner layout item yangilashi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/partner/layout-items/{self.layout_item.id}/"
        data = {"name": "Updated Table", "x": 150, "y": 250}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.layout_item.refresh_from_db()
        self.assertEqual(self.layout_item.name, "Updated Table")

    def test_partner_layout_item_delete_owner(self):
        """36. Owner layout item o'chirishi"""
        self.client.force_authenticate(user=self.owner)
        url = f"/api/layouts/partner/layout-items/{self.layout_item.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LayoutItem.objects.filter(id=self.layout_item.id).exists())

    def test_partner_layout_item_manager_permission(self):
        """37. Manager layout item yarata olishi"""
        self.client.force_authenticate(user=self.manager)
        url = "/api/layouts/partner/layout-items/create/"
        data = {
            "floor": self.floor.id,
            "type": "cashier",
            "name": "Cashier Desk",
            "x": 50,
            "y": 50,
            "width": 30,
            "height": 30
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ============================================================
    # 7. PERMISSIONS TESTS
    # ============================================================

    def test_superadmin_full_access(self):
        """38. Superadmin hamma narsani ko'rishi"""
        self.client.force_authenticate(user=self.superadmin)
        url = "/api/layouts/partner/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_receptionist_can_view_but_not_create(self):
        """39. Receptionist ko'ra oladi, lekin yarata olmaydi"""
        # Ko'rish mumkin
        self.client.force_authenticate(user=self.receptionist)
        url = "/api/layouts/partner/layout-items/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Yarata olmaydi
        create_url = "/api/layouts/partner/floors/create/"
        data = {"branch": self.branch.id, "name": "New Floor"}
        response = self.client.post(create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_denied(self):
        """40. Authentifikatsiyasiz partner API ga kirish mumkin emas"""
        url = "/api/layouts/partner/floors/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LayoutItemValidationTests(TestCase):
    """LayoutItem validatsiyalari testlari"""

    def setUp(self):
        self.owner = User.objects.create_user(
            phone="+998901234567",
            password="testpass123",
            role=User.Role.OWNER
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
            address="Test Address"
        )
        
        self.floor = Floor.objects.create(
            branch=self.branch,
            name="Floor 1"
        )
        
        self.zone = Zone.objects.create(
            floor=self.floor,
            name="Zone A"
        )
        self.layout_item = LayoutItem.objects.create(
            floor=self.floor,
            type="table",
            x=0, y=0, width=10, height=10
        )

    def test_layout_item_min_coordinates(self):
        """41. Layout item minimal koordinatalari"""
        item = LayoutItem.objects.create(
            floor=self.floor,
            type="decor",
            x=0, y=0, width=1, height=1
        )
        self.assertEqual(item.x, 0)
        self.assertEqual(item.y, 0)

    def test_layout_item_max_coordinates(self):
        """42. Layout item katta koordinatalari"""
        item = LayoutItem.objects.create(
            floor=self.floor,
            type="decor",
            x=10000, y=10000, width=1000, height=1000
        )
        self.assertEqual(item.x, 10000)
        self.assertEqual(item.y, 10000)

    def test_layout_item_rotation_negative(self):
        """43. Layout item manfiy rotation"""
        item = LayoutItem.objects.create(
            floor=self.floor,
            type="decor",
            x=0, y=0, width=10, height=10,
            rotation=-45
        )
        self.assertEqual(item.rotation, -45)

    def test_layout_item_meta_json_default(self):
        """44. Layout item meta default dict"""
        self.assertEqual(self.layout_item.meta, {})

    def test_layout_item_meta_json_custom(self):
        """45. Layout item meta JSON field"""
        item = LayoutItem.objects.create(
            floor=self.floor,
            type="table",
            x=0, y=0, width=10, height=10,
            meta={"color": "red", "price": 100}
        )
        self.assertEqual(item.meta["color"], "red")
        self.assertEqual(item.meta["price"], 100)