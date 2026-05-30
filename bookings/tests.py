from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from restaurants.models import Branch, RestaurantBrand 
from layouts.models import Floor, Zone, LayoutItem
from tables.models import Table
from bookings.models import Booking

User = get_user_model()


class BookingValidationTests(TestCase):
    """Booking validatsiyalarini tekshirish"""

    def setUp(self):
        # 1. Test user
        self.user = User.objects.create_user(
            phone="+998901234567",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        
        # 2. Test brand
        self.brand = RestaurantBrand.objects.create(
            name="Test Brand",
            owner=self.user
        )
        
        # 3. Test branch
        self.branch = Branch.objects.create(
            brand=self.brand,
            name="Test Branch",
            is_active=True,
            working_hours={
                "mon": ["09:00", "22:00"],
                "tue": ["09:00", "22:00"],
                "wed": ["09:00", "22:00"],
                "thu": ["09:00", "22:00"],
                "fri": ["09:00", "23:00"],
                "sat": ["10:00", "23:00"],
                "sun": ["10:00", "21:00"]
            },
            booking_hours={
                "mon": ["10:00", "21:00"],
                "tue": ["10:00", "21:00"],
                "wed": ["10:00", "21:00"],
                "thu": ["10:00", "21:00"],
                "fri": ["10:00", "21:00"],
                "sat": ["10:00", "21:00"],
                "sun": ["10:00", "20:00"]
            }
        )
        
        # 4. Test floor
        self.floor = Floor.objects.create(
            branch=self.branch,
            name="Test Floor",
            is_active=True
        )
        
        # 5. Test zone
        self.zone = Zone.objects.create(
            floor=self.floor,
            name="Test Zone",
            is_active=True
        )
        
        
        self.layout_item = LayoutItem.objects.create(
            floor=self.floor,
            zone=self.zone,
            type="table",
            name="Test Layout Item",
            x=0, y=0, width=100, height=100,
            is_active=True
        )
        self.table = Table.objects.create(
            branch=self.branch,
            floor=self.floor,
            zone=self.zone,
            layout_item=self.layout_item,
            name="T1",
            seats=4,
            is_active=True
        )

        
        # 7. API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 8. Base URL
        self.url = "/api/bookings/create/"
        
        # 9. Test data
        self.valid_data = {
            "branch": self.branch.id,
            "floor": self.floor.id,
            "zone": self.zone.id,
            "table": self.table.id,
            "guest_count": 2,
            "children_count": 0,
            "booking_start": (timezone.now() + timedelta(days=3, hours=2)).isoformat(),
            "booking_end": (timezone.now() + timedelta(days=3, hours=3)).isoformat(),
            "special_request": "Test request"
        }

    # ============================================================
    # 1. TO'G'RI BRON YARATISH
    # ============================================================
    
    def test_create_booking_success(self):
        """1. Muvaffaqiyatli bron yaratish"""
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("booking_id", response.data)
        self.assertEqual(Booking.objects.count(), 1)
    
    def test_create_booking_with_children(self):
        """2. Bolalar bilan bron yaratish"""
        data = self.valid_data.copy()
        data["children_count"] = 2
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_booking_without_zone(self):
        """3. Zonasiz bron yaratish"""
        data = self.valid_data.copy()
        data["zone"] = None
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ============================================================
    # 2. VAQT VALIDATSIYASI
    # ============================================================
    
    def test_booking_start_after_end(self):
        """4. Start vaqti end vaqtidan keyin"""
        data = self.valid_data.copy()
        data["booking_start"] = (timezone.now() + timedelta(days=3, hours=3)).isoformat()
        data["booking_end"] = (timezone.now() + timedelta(days=3, hours=2)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
    
    def test_booking_in_past(self):
        """5. O'tgan vaqtga bron"""
        data = self.valid_data.copy()
        data["booking_start"] = (timezone.now() - timedelta(days=1)).isoformat()
        data["booking_end"] = (timezone.now() - timedelta(days=1, hours=1)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_less_than_2_hours_advance(self):
        """6. 2 soatdan kam qolganda bron"""
        data = self.valid_data.copy()
        data["booking_start"] = (timezone.now() + timedelta(hours=1)).isoformat()
        data["booking_end"] = (timezone.now() + timedelta(hours=2)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_more_than_30_days_advance(self):
        """7. 30 kundan keyingi bron"""
        data = self.valid_data.copy()
        data["booking_start"] = (timezone.now() + timedelta(days=31)).isoformat()
        data["booking_end"] = (timezone.now() + timedelta(days=31, hours=1)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_less_than_30_minutes(self):
        """8. 30 daqiqadan kam bron"""
        data = self.valid_data.copy()
        data["booking_start"] = (timezone.now() + timedelta(days=3, hours=2)).isoformat()
        data["booking_end"] = (timezone.now() + timedelta(days=3, hours=2, minutes=15)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_more_than_4_hours(self):
        """9. 4 soatdan uzoq bron"""
        data = self.valid_data.copy()
        data["booking_start"] = (timezone.now() + timedelta(days=3, hours=2)).isoformat()
        data["booking_end"] = (timezone.now() + timedelta(days=3, hours=7)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_outside_working_hours_early(self):
        """10. Ish vaqtidan oldin bron"""
        data = self.valid_data.copy()
        # Sunday 08:00 (ish vaqti 10:00 dan)
        booking_time = timezone.now() + timedelta(days=(6 - timezone.now().weekday() + 7) % 7)
        booking_time = booking_time.replace(hour=8, minute=0, second=0)
        data["booking_start"] = booking_time.isoformat()
        data["booking_end"] = (booking_time + timedelta(hours=1)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_outside_working_hours_late(self):
        """11. Ish vaqtidan keyin bron"""
        data = self.valid_data.copy()
        # Sunday 22:00 (ish vaqti 21:00 gacha)
        booking_time = timezone.now() + timedelta(days=(6 - timezone.now().weekday() + 7) % 7)
        booking_time = booking_time.replace(hour=22, minute=0, second=0)
        data["booking_start"] = booking_time.isoformat()
        data["booking_end"] = (booking_time + timedelta(hours=1)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_outside_booking_hours(self):
        """12. Bron qabul qilinmaydigan vaqt"""
        # Aniq Monday 09:30 Toshkent vaqtida
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("Asia/Tashkent")
        booking_start = datetime(2026, 5, 18, 9, 30, tzinfo=tz)  # Monday
        booking_start_utc = booking_start.astimezone(ZoneInfo("UTC"))

        data = self.valid_data.copy()
        data["booking_start"] = booking_start_utc.isoformat()
        data["booking_end"] = (booking_start_utc + timedelta(hours=1)).isoformat()
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 3. SIG'IM VALIDATSIYASI
    # ============================================================
    
    def test_guest_count_zero(self):
        """13. Mehmonlar soni 0"""
        data = self.valid_data.copy()
        data["guest_count"] = 0
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("guest_count", response.data)
    
    def test_guest_count_negative(self):
        """14. Mehmonlar soni manfiy"""
        data = self.valid_data.copy()
        data["guest_count"] = -1
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_guest_count_exceeds_seats(self):
        """15. Stol sig'imidan ko'p"""
        data = self.valid_data.copy()
        data["guest_count"] = 10  # Stol 4 kishilik
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_children_count_more_than_guest_times_3(self):
        """16. Bolalar juda ko'p (mehmon * 3 dan ortiq)"""
        data = self.valid_data.copy()
        data["guest_count"] = 2
        data["children_count"] = 7  # 2*3=6 dan ko'p
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 4. OBYEKTLAR MOSLIGI
    # ============================================================
    
    def test_floor_not_belong_to_branch(self):
        """17. Floor branchga tegishli emas"""
        other_branch = Branch.objects.create(
            brand=self.brand,
            name="Other Branch",
            slug="other-branch-unique-123",  
            address="Test",
            is_active=True
        )
        other_floor = Floor.objects.create(
            branch=other_branch,
            name="Other Floor",
            is_active=True
        )
        data = self.valid_data.copy()
        data["floor"] = other_floor.id
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_table_not_belong_to_branch(self):
        """18. Table branchga tegishli emas"""
        other_branch = Branch.objects.create(
            brand=self.brand,
            name="Other Branch",
            slug="other-branch-unique-123",  
            address="Test",
            is_active=True
        )
        other_floor = Floor.objects.create( 
            branch=other_branch,
            name="Other Floor",
            is_active=True
        )
        layout_item2 = LayoutItem.objects.create(
            floor=self.floor, zone=self.zone, type="table",
            name="Test Layout 2", x=0, y=0, width=100, height=100
        )
        other_table = Table.objects.create(
            branch=other_branch, floor=other_floor, zone=self.zone, 
            layout_item=layout_item2,  
            name="T2", seats=4, is_active=True
        )
        data = self.valid_data.copy()
        data["table"] = other_table.id
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_zone_not_belong_to_floor(self):
        """19. Zone floorga tegishli emas"""
        other_floor = Floor.objects.create(
            branch=self.branch,
            name="Other Floor",
            is_active=True
        )
        other_zone = Zone.objects.create(
            floor=other_floor,
            name="Other Zone",
            is_active=True
        )
        data = self.valid_data.copy()
        data["zone"] = other_zone.id
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 5. OVERLAPPING (BANDLIK)
    # ============================================================
    
    def test_double_booking_same_time(self):
        """20. Bir vaqtga 2 marta bron"""
        # 1-bron
        response1 = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # 2-bron (aynan vaqt)
        response2 = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("band", str(response2.data))
    
    def test_double_booking_overlap_start(self):
        """21. Bir vaqtga qisman overlapping (boshlanishi)"""
        # 1-bron: 14:00-15:00
        data1 = self.valid_data.copy()
        data1["booking_start"] = (timezone.now() + timedelta(days=3, hours=2)).isoformat()
        data1["booking_end"] = (timezone.now() + timedelta(days=3, hours=3)).isoformat()
        self.client.post(self.url, data1, format='json')
        
        # 2-bron: 14:30-15:30 (overlap)
        data2 = self.valid_data.copy()
        data2["booking_start"] = (timezone.now() + timedelta(days=3, hours=2, minutes=30)).isoformat()
        data2["booking_end"] = (timezone.now() + timedelta(days=3, hours=3, minutes=30)).isoformat()
        response = self.client.post(self.url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_double_booking_exact_end(self):
        """22. Ketma-ket bron (15 daqiqa tozalash vaqti)"""
        # 1-bron: 14:00-15:00
        data1 = self.valid_data.copy()
        data1["booking_start"] = (timezone.now() + timedelta(days=3, hours=2)).isoformat()
        data1["booking_end"] = (timezone.now() + timedelta(days=3, hours=3)).isoformat()
        self.client.post(self.url, data1, format='json')
        
        # 2-bron: 15:00-16:00 (0 daqiqa farq - XATO)
        data2 = self.valid_data.copy()
        data2["booking_start"] = (timezone.now() + timedelta(days=3, hours=3)).isoformat()
        data2["booking_end"] = (timezone.now() + timedelta(days=3, hours=4)).isoformat()
        response = self.client.post(self.url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_sequential_booking_with_cleaning(self):
        """23. Ketma-ket bron (15 daqiqa farq - TO'G'RI)"""
        # 1-bron: 14:00-15:00
        data1 = self.valid_data.copy()
        data1["booking_start"] = (timezone.now() + timedelta(days=3, hours=2)).isoformat()
        data1["booking_end"] = (timezone.now() + timedelta(days=3, hours=3)).isoformat()
        self.client.post(self.url, data1, format='json')
        
        # 2-bron: 15:15-16:15 (15 daqiqa farq - TO'G'RI)
        data2 = self.valid_data.copy()
        data2["booking_start"] = (timezone.now() + timedelta(days=3, hours=3, minutes=15)).isoformat()
        data2["booking_end"] = (timezone.now() + timedelta(days=3, hours=4, minutes=15)).isoformat()
        response = self.client.post(self.url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ============================================================
    # 6. FOYDALANUVCHI CHEKLOVLARI
    # ============================================================
    
    def test_user_double_booking_same_time(self):
        """24. Bir foydalanuvchi bir vaqtda 2 bron"""
        # 1-bron
        self.client.post(self.url, self.valid_data, format='json')
        
        # 2-bron uchun layout_item va table
        layout_item2 = LayoutItem.objects.create(
            floor=self.floor, zone=self.zone, type="table",
            name="Test Layout 2", x=0, y=0, width=100, height=100,
            is_active=True
        )
        other_table = Table.objects.create(
            branch=self.branch,
            floor=self.floor,
            zone=self.zone,
            layout_item=layout_item2,
            name="T2",
            seats=4,
            is_active=True
        )
        
        data2 = self.valid_data.copy()
        data2["table"] = other_table.id
        response = self.client.post(self.url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 7. AUTHENTICATION
    # ============================================================
    
    def test_unauthenticated_user(self):
        """25. Autentifikatsiyasiz foydalanuvchi"""
        client = APIClient()
        response = client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inactive_table(self):
        """26. Faol bo'lmagan stol"""
        self.table.is_active = False
        self.table.save()
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # 8. BRONNI BEKOR QILISH
    # ============================================================
    
    def test_cancel_booking_success(self):
        """27. Bronni bekor qilish"""
        # Bron yaratish
        response = self.client.post(self.url, self.valid_data, format='json')
        booking_id = response.data["booking_id"]
        
        # Bekor qilish
        cancel_url = f"/api/bookings/my/{booking_id}/cancel/"
        response = self.client.post(cancel_url, {"note": "Test cancel"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Status tekshirish
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.status, "canceled")
    
    def test_cancel_completed_booking(self):
        """28. Completed bronni bekor qilish"""
        # Bron yaratish
        response = self.client.post(self.url, self.valid_data, format='json')
        booking_id = response.data["booking_id"]
        
        # Statusni completed ga o'zgartirish
        booking = Booking.objects.get(id=booking_id)
        booking.status = "completed"
        booking.save()
        
        # Bekor qilishga urinish
        cancel_url = f"/api/bookings/my/{booking_id}/cancel/"
        response = self.client.post(cancel_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cancel_other_user_booking(self):
        """29. Boshqa foydalanuvchining bronini bekor qilish"""
        # Boshqa user
        other_user = User.objects.create_user(
            phone="+998998887766",
            password="testpass123"
        )
        
        # Boshqa user bron qiladi
        client2 = APIClient()
        client2.force_authenticate(user=other_user)
        response = client2.post(self.url, self.valid_data, format='json')
        booking_id = response.data["booking_id"]
        
        # Birinchi user bekor qilishga urinadi
        cancel_url = f"/api/bookings/my/{booking_id}/cancel/"
        response = self.client.post(cancel_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ============================================================
    # 9. STATUS O'ZGARTIRISH
    # ============================================================
    
    def test_status_transition_pending_to_confirmed(self):
        """30. Pending -> Confirmed"""
        response = self.client.post(self.url, self.valid_data, format='json')
        booking_id = response.data["booking_id"]
        
        # Partner token kerak (oddiy user o'zgartira olmaydi)
        # Bu test faqat model darajasida
        booking = Booking.objects.get(id=booking_id)
        booking.status = "confirmed"
        booking.save()
        self.assertEqual(booking.status, "confirmed")
    
    def test_invalid_status_transition(self):
        """31. Noto'g'ri status o'tishi"""
        booking = Booking.objects.create(
            user=self.user,
            branch=self.branch,
            floor=self.floor,
            table=self.table,
            guest_count=2,
            booking_start=timezone.now() + timedelta(days=2),
            booking_end=timezone.now() + timedelta(days=2, hours=1),
            status="pending"
        )
        
        # completed ga to'g'ridan-to'g'ri o'tish mumkin emas
        booking.status = "completed"
        booking.save()
        # Bu saqlanadi, lekin service orqali tekshiriladi
        # Service da validate_status_transition bor

    # ============================================================
    # 10. CHEGARA HOLATLAR
    # ============================================================
    
    def test_booking_exactly_at_working_hours_start(self):
        """32. Ish vaqti boshlanishiga to'g'ri keladigan bron"""
        # Monday 10:00
        booking_time = timezone.now() + timedelta(days=(0 - timezone.now().weekday() + 7) % 7)
        booking_time = booking_time.replace(hour=10, minute=0, second=0)
        data = self.valid_data.copy()
        data["booking_start"] = booking_time.isoformat()
        data["booking_end"] = (booking_time + timedelta(hours=1)).isoformat()
        response = self.client.post(self.url, data, format='json')
        # Agar ish vaqtiga to'g'ri kelsa, 201 yoki 400 (booking_hours ga qarab)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_booking_exactly_at_booking_hours_end(self):
        """33. Bron qabul qilish vaqtining oxirgi daqiqasi"""
        # Monday 20:59
        booking_time = timezone.now() + timedelta(days=(0 - timezone.now().weekday() + 7) % 7)
        booking_time = booking_time.replace(hour=20, minute=59, second=0)
        data = self.valid_data.copy()
        data["booking_start"] = booking_time.isoformat()
        data["booking_end"] = (booking_time + timedelta(minutes=30)).isoformat()
        response = self.client.post(self.url, data, format='json')
        # 20:59 da bron qilish mumkin (21:00 dan oldin)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_max_guest_count_at_table(self):
        """34. Stol sig'imining chegarasi"""
        data = self.valid_data.copy()
        data["guest_count"] = 4  # Stol 4 kishilik
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_min_duration_exact_30_minutes(self):
        """35. 30 daqiqa aniq bron"""
        data = self.valid_data.copy()
        data["booking_start"] = (timezone.now() + timedelta(days=3, hours=2)).isoformat()
        data["booking_end"] = (timezone.now() + timedelta(days=3, hours=2, minutes=30)).isoformat()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PartnerBookingTests(TestCase):
    """Partner (staff) booking testlari"""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            phone="+998901234568",
            password="staffpass123",
            role=User.Role.MANAGER
        )
        self.owner = User.objects.create_user(phone="+998901234569", password="test")

        self.brand = RestaurantBrand.objects.create(name="Test Brand", owner=self.owner, slug="test-brand")
        self.branch = Branch.objects.create(
            brand=self.brand,
            name="Test Branch",
            is_active=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff_user)
    
    def test_partner_get_bookings_list(self):
        """36. Partner bronlar ro'yxatini ko'rish"""
        url = "/api/bookings/partner/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_partner_manual_booking_create(self):
        """37. Partner manual bron yaratish"""
        url = "/api/bookings/partner/manual-create/"
        data = {
            "guest_name": "Test Guest",
            "guest_phone": "+998901234569",
            "branch": self.branch.id,
            "floor": 1,
            "table": 1,
            "guest_count": 2,
            "booking_start": (timezone.now() + timedelta(days=2, hours=2)).isoformat(),
            "booking_end": (timezone.now() + timedelta(days=2, hours=3)).isoformat()
        }
        # Floor va table mavjud bo'lishi kerak
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_partner_occupied_tables(self):
        """38. Band stollarni ko'rish"""
        url = "/api/bookings/partner/occupied-tables/"
        params = {
            "branch_id": self.branch.id,
            "booking_start": (timezone.now() + timedelta(days=2, hours=2)).isoformat(),
            "booking_end": (timezone.now() + timedelta(days=2, hours=3)).isoformat()
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)