from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ConsumerRequestRegisterOTPSerializer,
    ConsumerRegisterSerializer,
    LoginSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordConfirmSerializer,
    ProfileUpdateSerializer,
    UserSerializer,
    OwnerCreateSerializer,
    ManagerCreateSerializer,
    EmailPasswordLoginSerializer,
)
from .permissions import IsSuperAdmin, IsOwnerOrSuperAdmin


def build_auth_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data
    }


class ConsumerRequestRegisterOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConsumerRequestRegisterOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Telegram kod yuborildi"}, status=status.HTTP_200_OK)


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
        return Response({"detail": "Reset kodi Telegramga yuborildi"}, status=status.HTTP_200_OK)


class ForgotPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Parol yangilandi"}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class OwnerCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = OwnerCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class ManagerCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def post(self, request):
        serializer = ManagerCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class PartnerLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailPasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)