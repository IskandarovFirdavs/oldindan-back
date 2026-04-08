from django.urls import path
from .views import (
    MyBookingListView,
    MyBookingDetailView,
    ConsumerBookingCreateView,
    MyBookingCancelView,
    PartnerBookingListView,
    PartnerBookingDetailView,
    PartnerManualBookingCreateView,
    PartnerBookingStatusUpdateView,
    PartnerOccupiedTablesView,
)

urlpatterns = [
    # consumer
    path("my/", MyBookingListView.as_view(), name="my-booking-list"),
    path("my/<int:pk>/", MyBookingDetailView.as_view(), name="my-booking-detail"),
    path("create/", ConsumerBookingCreateView.as_view(), name="consumer-booking-create"),
    path("my/<int:pk>/cancel/", MyBookingCancelView.as_view(), name="my-booking-cancel"),

    # partner
    path("partner/", PartnerBookingListView.as_view(), name="partner-booking-list"),
    path("partner/<int:pk>/", PartnerBookingDetailView.as_view(), name="partner-booking-detail"),
    path("partner/manual-create/", PartnerManualBookingCreateView.as_view(), name="partner-manual-booking-create"),
    path("partner/<int:pk>/status/", PartnerBookingStatusUpdateView.as_view(), name="partner-booking-status-update"),
    path("partner/occupied-tables/", PartnerOccupiedTablesView.as_view(), name="partner-occupied-tables"),
]