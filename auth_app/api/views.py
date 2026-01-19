from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .serializers import RegistrationSerializer, LoginTokenObtainPairSerializer, PasswordConfirmSerializer
from auth_app.signals import user_registered, password_reset
from .permissions import IsOwner


class RegistrationView(APIView):
    """
    Handle user registration requests.
    Creates an inactive user and sends an activation email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        token = self._generate_activation_token(user)
        self._send_activation_email(user, token)

        return Response(
            self._build_response(user, token),
            status=status.HTTP_201_CREATED
        )

    def _generate_activation_token(self, user):
        return default_token_generator.make_token(user)

    def _send_activation_email(self, user, token):
        user_registered.send(
            sender=self.__class__,
            user=user,
            token=token
        )

    def _build_response(self, user, token):
        return {
            "user": {
                "id": user.id,
                "email": user.email,
            },
            "token": token,
        }


class ActivateAccountView(APIView):
    """
    Activate a user account using a UID and token.
    Validates the activation link and enables the account.
    """
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token, *args, **kwargs):
        user = self._get_user_from_uid(uidb64)

        if not user:
            return Response(
                {"error": "Invalid user."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not self._is_token_valid(user, token):
            return Response(
                {"error": "Activation link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        self._activate_user(user)

        return Response(
            {"message": "Account successfully activated."},
            status=status.HTTP_200_OK
        )

    def _get_user_from_uid(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return None

    def _is_token_valid(self, user, token):
        return default_token_generator.check_token(user, token)

    def _activate_user(self, user):
        user.is_active = True
        user.save(update_fields=["is_active"])


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Authenticate a user and issue JWT tokens via HTTP-only cookies.
    Uses email/password validation before token generation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validate credentials and set access/refresh tokens as cookies.
        """
        serializer = LoginTokenObtainPairSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response(
            {
                "detail": "Login successfully!",
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        return response
    

class CookieTokenRefreshView(TokenRefreshView):
    """
    Refresh the JWT access token using a refresh token from cookies.
    Issues a new access token if the refresh token is valid.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Validate refresh token and update the access token cookie.
        """
        refresh = request.COOKIES.get("refresh_token")

        if refresh is None:
            return Response(
                {'detail': 'Refresh token not found!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data={'refresh':refresh})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {'detail': 'Refresh token invalid!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        access_token = serializer.validated_data.get("access")

        response = Response(
            {
                'detail': 'Token refreshed',
                'access': access_token
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax",
        )

        return response
    

class LogoutView(APIView):
    """
    Log out the current user.
    Blacklists the refresh token and clears authentication cookies.
    """
    permission_classes = [IsOwner]

    def post(self, request):
        """
        Invalidate refresh token and remove access/refresh cookies.
        """
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            print(f"Failed to move the token to the blacklist: {e}")

        response = Response(
            {
                "detail": (
                    "Log-Out successfully! All Tokens will be deleted. "
                    "Refresh token is now invalid."
                )
            },
            status=status.HTTP_200_OK,
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    

class PasswordResetView(APIView):
    """
    Handles password reset requests safely without revealing user existence.
    Always returns a success response for security.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validates email and triggers a password reset if user exists.
        Returns a generic success response regardless of outcome.
        """
        email = request.data.get("email")

        error_response = self._validate_email(email)
        if error_response:
            return error_response

        self._send_password_reset(email)

        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK
        )

    def _validate_email(self, email):
        """
        Checks if email is provided and properly formatted.
        Returns an error Response or None if valid.
        """
        if not email:
            return Response(
                {"email": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"email": "Enter a valid email address."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return None

    def _send_password_reset(self, email):
        """
        Generates a reset token and sends the password_reset signal.
        Does nothing if the user with the email does not exist.
        """
        user = User.objects.filter(email=email).first()
        if not user:
            return

        token = default_token_generator.make_token(user)

        password_reset.send(
            sender=self.__class__,
            user=user,
            token=token,
        )
        

class PasswordResetConfirmView(APIView):
    """
    Confirm a password reset using UID and token.
    Sets a new password after successful validation.
    """
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """
        Validate reset data, token, and update the user password.
        Returns success or error responses based on validation.
        """
        serializer = PasswordConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return self._response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = self._get_user(uidb64)
        error_response = self._validate_user_and_token(user, token)
        if error_response:
            return error_response

        self._update_password(user, serializer.validated_data['new_password'])
        return self._response(
            {"detail": "Your password has been successfully reset."},
            status.HTTP_200_OK
        )

    def _get_user(self, uidb64):
        """
        Decode UID and return the associated user or None.
        """
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def _validate_user_and_token(self, user, token):
        """
        Check if the user exists and the token is valid.
        Returns an error Response if invalid, otherwise None.
        """
        if user is None:
            return self._response({"error": "Invalid reset link."}, status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return self._response({"error": "Invalid or expired reset link."}, status.HTTP_400_BAD_REQUEST)

        return None

    def _update_password(self, user, new_password):
        """
        Set and save the user's new password securely.
        """
        user.set_password(new_password)
        user.save(update_fields=['password'])

    def _response(self, data, status_code):
        """
        Helper method to create Response objects consistently.
        """
        return Response(data, status=status_code)