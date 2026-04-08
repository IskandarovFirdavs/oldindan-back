from django.urls import path
from .views import (
    PartnerStaffListView,
    PartnerStaffCreateView,
    PartnerStaffDetailView,
    MyStaffMembershipListView,
)

urlpatterns = [
    path("partner/staff/", PartnerStaffListView.as_view(), name="partner-staff-list"),
    path("partner/staff/create/", PartnerStaffCreateView.as_view(), name="partner-staff-create"),
    path("partner/staff/<int:pk>/", PartnerStaffDetailView.as_view(), name="partner-staff-detail"),

    path("my-memberships/", MyStaffMembershipListView.as_view(), name="my-staff-memberships"),
]