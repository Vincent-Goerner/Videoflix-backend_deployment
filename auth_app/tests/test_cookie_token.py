from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status


class CookieTokenTest(APITestCase):
    """
    Test cases for cookie-based JWT login.
    Verifies successful authentication and error handling.
    """
    def setUp(self):
        """
        Create a test user and define the login URL.
        """
        self.url = reverse('login')
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpassword"
        )

    def test_post_login_successful(self):
        """
        Ensure valid credentials return tokens as secure HTTP-only cookies.
        """
        data = {
            "email": "test@example.com",
            "password": "testpassword"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("detail", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "test@example.com")

        cookies = response.cookies
        self.assertIn("access_token", cookies)
        self.assertIn("refresh_token", cookies)

        access_cookie = cookies["access_token"]
        refresh_cookie = cookies["refresh_token"]

        self.assertTrue(access_cookie["httponly"])
        self.assertTrue(refresh_cookie["httponly"])
        self.assertTrue(access_cookie["secure"])
        self.assertTrue(refresh_cookie["secure"])
    
    def test_post_login_invalid_credentials(self):
        """
        Ensure invalid credentials return 401 and no cookies.
        """
        data = {"email": "test@example.com", "password": "testpassword2"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

    def test_post_login_missing_fields(self):
        """
        Ensure missing required fields return validation errors.
        """
        data = {"email": "test@example.com",}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertIn("password", response.data)
        self.assertEqual(response.data["password"][0], "This field is required.")