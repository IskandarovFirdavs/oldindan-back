from django.urls import path
from .views import (
    PublicBranchTableListView,
    PartnerTableListView,
    PartnerTableCreateView,
    PartnerTableDetailView,
)

urlpatterns = [
    # public / consumer
    path("branches/<int:branch_id>/tables/", PublicBranchTableListView.as_view(), name="public-branch-tables"),

    # partner
    path("partner/tables/", PartnerTableListView.as_view(), name="partner-table-list"),
    path("partner/tables/create/", PartnerTableCreateView.as_view(), name="partner-table-create"),
    path("partner/tables/<int:pk>/", PartnerTableDetailView.as_view(), name="partner-table-detail"),
]