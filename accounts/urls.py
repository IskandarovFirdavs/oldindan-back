from django.urls import path

from .views import (
    ConsumerLoginView,
    ConsumerRegisterView,
    ConsumerRequestRegisterOTPView,
    ForgotPasswordConfirmView,
    ForgotPasswordRequestView,
    MeView,
    OwnerCreateView,
    PartnerLoginView,
    StaffCreateView,
)

urlpatterns = [
    # consumer
    path("consumer/request-otp/", ConsumerRequestRegisterOTPView.as_view()),
    path("consumer/register/", ConsumerRegisterView.as_view()),
    path("consumer/login/", ConsumerLoginView.as_view()),
    path("consumer/forgot-password/request/", ForgotPasswordRequestView.as_view()),
    path("consumer/forgot-password/confirm/", ForgotPasswordConfirmView.as_view()),

    # profile
    path("me/", MeView.as_view()),

    # partner / admin
    path("partner/login/", PartnerLoginView.as_view()),
    path("partner/create-owner/", OwnerCreateView.as_view()),
    path("partner/create-staff/", StaffCreateView.as_view()),
]