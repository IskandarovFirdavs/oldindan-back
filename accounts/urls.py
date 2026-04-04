from django.urls import path
from .views import (
    ConsumerRequestRegisterOTPView,
    ConsumerRegisterView,
    ConsumerLoginView,
    ForgotPasswordRequestView,
    ForgotPasswordConfirmView,
    MeView,
    OwnerCreateView,
    ManagerCreateView,
    PartnerLoginView,
)

urlpatterns = [
    # consumer
    path("consumer/request-register-otp/", ConsumerRequestRegisterOTPView.as_view()),
    path("consumer/register/", ConsumerRegisterView.as_view()),
    path("consumer/login/", ConsumerLoginView.as_view()),
    path("consumer/forgot-password/request/", ForgotPasswordRequestView.as_view()),
    path("consumer/forgot-password/confirm/", ForgotPasswordConfirmView.as_view()),

    # profile
    path("me/", MeView.as_view()),

    # partner / admin
    path("partner/login/", PartnerLoginView.as_view()),
    path("partner/create-owner/", OwnerCreateView.as_view()),
    path("partner/create-manager/", ManagerCreateView.as_view()),
]