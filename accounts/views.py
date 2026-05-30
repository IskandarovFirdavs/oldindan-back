from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .permissions import IsSuperAdmin, IsOwnerOrSuperAdmin, IsOwnerOrManager
from .serializers import (
    ConsumerRequestRegisterOTPSerializer,
    ConsumerRegisterSerializer,
    LoginSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordConfirmSerializer,
    OwnerCreateSerializer,
    PartnerLoginSerializer,
    ProfileUpdateSerializer,
    StaffCreateSerializer,
    UserSerializer,
)


def build_auth_response(user: User) -> dict:
    """JWT tokenlar va user ma'lumotlarini qaytaradi."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data,
    }


# ---------------------------------------------------------------------------
# CONSUMER
# ---------------------------------------------------------------------------

class ConsumerRequestRegisterOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConsumerRequestRegisterOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "SMS kod yuborildi."}, status=status.HTTP_200_OK)


class ConsumerRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConsumerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(build_auth_response(user), status=status.HTTP_201_CREATED)


class ConsumerLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class ForgotPasswordRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "SMS kod yuborildi."}, status=status.HTTP_200_OK)


class ForgotPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Parol muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


# ---------------------------------------------------------------------------
# PARTNER
# ---------------------------------------------------------------------------

class PartnerLoginView(APIView):
    """
    Owner, superadmin va BranchStaff (manager, receptionist, waiter, waitress)
    uchun email/password login.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PartnerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class OwnerCreateView(APIView):
    """Faqat Superadmin yangi Owner yaratadi."""
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = OwnerCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class StaffCreateView(APIView):
    """
    Owner yoki Manager tomonidan staff yaratish.
    Role: manager, receptionist, waiter, waitress.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request):
        serializer = StaffCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)