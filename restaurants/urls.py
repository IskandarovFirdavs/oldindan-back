from django.urls import path
from .views import (
    PublicBranchListView,
    PublicBranchDetailView,
    PartnerBrandListView,
    PartnerBrandCreateView,
    PartnerBranchListView,
    PartnerBranchCreateView,
    PartnerBranchDetailView,
    PartnerBranchImageCreateView,
)

urlpatterns = [
    # consumer
    path("branches/", PublicBranchListView.as_view(), name="public-branch-list"),
    path("branches/<int:pk>/", PublicBranchDetailView.as_view(), name="public-branch-detail"),

    # partner brands
    path("partner/brands/", PartnerBrandListView.as_view(), name="partner-brand-list"),
    path("partner/brands/create/", PartnerBrandCreateView.as_view(), name="partner-brand-create"),

    # partner branches
    path("partner/branches/", PartnerBranchListView.as_view(), name="partner-branch-list"),
    path("partner/branches/create/", PartnerBranchCreateView.as_view(), name="partner-branch-create"),
    path("partner/branches/<int:pk>/", PartnerBranchDetailView.as_view(), name="partner-branch-detail"),
    path("partner/branch-images/create/", PartnerBranchImageCreateView.as_view(), name="partner-branch-image-create"),
]