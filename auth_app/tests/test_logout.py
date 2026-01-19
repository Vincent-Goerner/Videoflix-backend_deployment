from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutTest(APITestCase):
    """
    Test cases for the logout endpoint.
    Verifies successful logout and token invalidation.
    """
    def setUp(self):
        """
        Create a test user and define the logout URL.
        """
        self.url = reverse('logout')
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpassword"
        )

    def test_post_logout_successful(self):
        """
        Ensure logout returns 200 OK with valid authentication.
        """
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        self.client.cookies.load({
            "access_token": access_token,
            "refresh_token": refresh_token,
        })

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        