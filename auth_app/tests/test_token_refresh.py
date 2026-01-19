from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


class CookieTokenRefreshTest(APITestCase):
    """
    Test cases for refreshing JWT access tokens via cookies.
    Verifies valid, missing, and invalid refresh token scenarios.
    """
    def setUp(self):
        """
        Create a test user and generate access/refresh tokens.
        """
        self.url = reverse('token-refresh')
        self.user = User.objects.create_user(
           username="test@example.com", email="test@example.com", password="testpassword"
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)
    
    def test_post_refresh_token_successful(self):
        """
        Ensure a valid refresh token returns a new access token.
        """
        self.client.cookies.load({"refresh_token": self.refresh_token})

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("access", response.data)
        self.assertIn("access_token", response.cookies)
        self.assertEqual(response.cookies["access_token"].value, response.data["access"])
    
    def test_post_refresh_token_missing(self):
        """
        Ensure a missing refresh token returns a 400 error.
        """
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_refresh_token_invalid(self):
        """
        Ensure an invalid refresh token returns a 401 error.
        """
        self.client.cookies["refresh_token"] = "invalidtoken"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)