from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


class ActivateAccountViewTest(APITestCase):
    """
    Test cases for the account activation API view.
    Verifies successful activation and error handling.
    """
    def setUp(self):
        """
        Create an inactive test user and generate UID/token.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            is_active=False
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def test_get_activate_account_success(self):
        """
        Ensure a valid activation link activates the user.
        """
        url = reverse('activate', kwargs={'uidb64': self.uidb64, 'token': self.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Account successfully activated.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_get_activate_account_invalid_token(self):
        """
        Ensure an invalid token returns a 400 error.
        """
        url = reverse('activate', kwargs={'uidb64': self.uidb64, 'token': 'wrongtoken'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Activation link is invalid", response.data['error'])

    def test_get_activate_account_invalid_user(self):
        """
        Ensure an invalid UID returns an error response.
        """
        url = reverse('activate', kwargs={'uidb64': 'MTIz', 'token': self.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Invalid user.")