from django.urls import path
from .views import (
    ConsumerRequestRegisterOTPView, ConsumerRegisterView, ConsumerLoginView,
    ConsumerForgotPasswordRequestView, ConsumerForgotPasswordConfirmView,
    OwnerRegisterView, OwnerLoginView, OwnerForgotPasswordRequestView, OwnerForgotPasswordConfirmView,
    StaffRegisterView, StaffLoginView, StaffForgotPasswordRequestView, StaffForgotPasswordConfirmView,
    MeView, OwnerCreateBySuperadminView,
)

urlpatterns = [
    # consumer
    path("consumer/request-register-otp/", ConsumerRequestRegisterOTPView.as_view()),
    path("consumer/register/", ConsumerRegisterView.as_view()),
    path("consumer/login/", ConsumerLoginView.as_view()),
    path("consumer/forgot-password/request/", ConsumerForgotPasswordRequestView.as_view()),
    path("consumer/forgot-password/confirm/", ConsumerForgotPasswordConfirmView.as_view()),

    # owner
    path("owner/register/", OwnerRegisterView.as_view()),
    path("owner/login/", OwnerLoginView.as_view()),
    path("owner/forgot-password/request/", OwnerForgotPasswordRequestView.as_view()),
    path("owner/forgot-password/confirm/", OwnerForgotPasswordConfirmView.as_view()),

    # manager / receptionist (staff)
    path("staff/register/", StaffRegisterView.as_view()),
    path("staff/login/", StaffLoginView.as_view()),
    path("staff/forgot-password/request/", StaffForgotPasswordRequestView.as_view()),
    path("staff/forgot-password/confirm/", StaffForgotPasswordConfirmView.as_view()),

    # profile
    path("me/", MeView.as_view()),

    # superadmin
    path("create-owner/", OwnerCreateBySuperadminView.as_view()),
]