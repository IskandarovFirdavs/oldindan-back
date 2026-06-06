from django.urls import path
from .views import (
    MyBookingListView,
    MyBookingDetailView,
    ConsumerBookingCreateView,
    MyBookingCancelView,
    TableSlotsView,
    AvailableSlotsView,
    PartnerBookingListView,
    PartnerBookingDetailView,
    PartnerManualBookingCreateView,
    PartnerBookingStatusUpdateView,
    PartnerCheckInByNumberView,
    PartnerMarkNoShowView,
    PartnerOccupiedTablesView,
    BookingMessageListView,
    BookingMessageCreateView,
)

urlpatterns = [
    # ── consumer ──────────────────────────────────────────────
    path("my/",                          MyBookingListView.as_view(),          name="my-booking-list"),
    path("my/<int:pk>/",                 MyBookingDetailView.as_view(),        name="my-booking-detail"),
    path("create/",                      ConsumerBookingCreateView.as_view(),  name="consumer-booking-create"),
    path("my/<int:pk>/cancel/",          MyBookingCancelView.as_view(),        name="my-booking-cancel"),

    # ── slot grid (new green/red system) ──────────────────────
    path("slots/",                       TableSlotsView.as_view(),             name="table-slots"),

    # ── available slots (legacy) ──────────────────────────────
    path("available-slots/",             AvailableSlotsView.as_view(),         name="available-slots"),

    # ── chat / messages ───────────────────────────────────────
    path("<int:pk>/messages/",           BookingMessageListView.as_view(),     name="booking-messages"),
    path("<int:pk>/messages/send/",      BookingMessageCreateView.as_view(),   name="booking-message-send"),

    # ── partner ───────────────────────────────────────────────
    path("partner/",                     PartnerBookingListView.as_view(),         name="partner-booking-list"),
    path("partner/<int:pk>/",            PartnerBookingDetailView.as_view(),       name="partner-booking-detail"),
    path("partner/manual-create/",       PartnerManualBookingCreateView.as_view(), name="partner-manual-booking-create"),
    path("partner/<int:pk>/status/",     PartnerBookingStatusUpdateView.as_view(), name="partner-booking-status-update"),
    path("partner/checkin/",             PartnerCheckInByNumberView.as_view(),     name="partner-checkin"),
    path("partner/<int:pk>/no-show/",    PartnerMarkNoShowView.as_view(),          name="partner-no-show"),
    path("partner/occupied-tables/",     PartnerOccupiedTablesView.as_view(),      name="partner-occupied-tables"),
]