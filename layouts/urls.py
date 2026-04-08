from django.urls import path
from .views import (
    PublicBranchFloorListView,
    PublicBranchLayoutItemsView,
    PartnerFloorListView,
    PartnerFloorCreateView,
    PartnerFloorDetailView,
    PartnerZoneCreateView,
    PartnerZoneDetailView,
    PartnerLayoutItemListView,
    PartnerLayoutItemCreateView,
    PartnerLayoutItemDetailView,
)

urlpatterns = [
    # public / consumer
    path("branches/<int:branch_id>/floors/", PublicBranchFloorListView.as_view(), name="public-branch-floors"),
    path("branches/<int:branch_id>/layout-items/", PublicBranchLayoutItemsView.as_view(), name="public-branch-layout-items"),

    # partner floors
    path("partner/floors/", PartnerFloorListView.as_view(), name="partner-floor-list"),
    path("partner/floors/create/", PartnerFloorCreateView.as_view(), name="partner-floor-create"),
    path("partner/floors/<int:pk>/", PartnerFloorDetailView.as_view(), name="partner-floor-detail"),

    # partner zones
    path("partner/zones/create/", PartnerZoneCreateView.as_view(), name="partner-zone-create"),
    path("partner/zones/<int:pk>/", PartnerZoneDetailView.as_view(), name="partner-zone-detail"),

    # partner layout items
    path("partner/layout-items/", PartnerLayoutItemListView.as_view(), name="partner-layout-item-list"),
    path("partner/layout-items/create/", PartnerLayoutItemCreateView.as_view(), name="partner-layout-item-create"),
    path("partner/layout-items/<int:pk>/", PartnerLayoutItemDetailView.as_view(), name="partner-layout-item-detail"),
]