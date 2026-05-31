from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .permissions import IsSuperAdmin
from .serializers import (
    ConsumerRequestRegisterOTPSerializer, ConsumerRegisterSerializer, ConsumerLoginSerializer,
    ConsumerForgotPasswordRequestSerializer, ConsumerForgotPasswordConfirmSerializer,
    OwnerRegisterSerializer, OwnerLoginSerializer, OwnerForgotPasswordRequestSerializer,
    OwnerForgotPasswordConfirmSerializer, OwnerCreateBySuperadminSerializer,
    StaffRegisterSerializer, StaffLoginSerializer, StaffForgotPasswordRequestSerializer,
    StaffForgotPasswordConfirmSerializer,
    ProfileUpdateSerializer, UserSerializer,
)


def build_auth_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data,
    }


# ----- CONSUMER -----
class ConsumerRequestRegisterOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = ConsumerRequestRegisterOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "OTP sent."}, status=status.HTTP_200_OK)


class ConsumerRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = ConsumerRegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(build_auth_response(user), status=status.HTTP_201_CREATED)


class ConsumerLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = ConsumerLoginSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class ConsumerForgotPasswordRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = ConsumerForgotPasswordRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "OTP sent."}, status=status.HTTP_200_OK)


class ConsumerForgotPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = ConsumerForgotPasswordConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)


# ----- OWNER -----
class OwnerRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = OwnerRegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(build_auth_response(user), status=status.HTTP_201_CREATED)


class OwnerLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = OwnerLoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class OwnerForgotPasswordRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = OwnerForgotPasswordRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "OTP sent."}, status=status.HTTP_200_OK)


class OwnerForgotPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = OwnerForgotPasswordConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)


# ----- MANAGER / RECEPTIONIST (STAFF) -----
class StaffRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = StaffRegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(build_auth_response(user), status=status.HTTP_201_CREATED)


class StaffLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = StaffLoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class StaffForgotPasswordRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = StaffForgotPasswordRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "OTP sent."}, status=status.HTTP_200_OK)


class StaffForgotPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = StaffForgotPasswordConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)


# ----- PROFILE -----
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user).data)
    def patch(self, request):
        s = ProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(UserSerializer(request.user).data)


# ----- SUPERADMIN CREATE OWNER -----
class OwnerCreateBySuperadminView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def post(self, request):
        s = OwnerCreateBySuperadminSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)