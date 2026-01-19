from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from rest_framework import status
from rest_framework.test import APITestCase

from unittest.mock import patch


class PasswordResetTests(APITestCase):
    """
    Tests password reset requests, verifying email sending and input validation.
    """
    def setUp(self):
        """
        Sets up a test user and password reset URLs.
        """
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="OldPassword123"
        )
        self.reset_url = reverse('password-reset')
        self.confirm_url_name = 'password-reset-confirm'

    @patch('auth_app.signals.send_email')
    def test_password_reset_email_sent_for_existing_user(self, mock_send_email):
        """
        Verifies that a reset email is sent for an existing user.
        """
        data = {'email': self.user.email}
        response = self.client.post(self.reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        mock_send_email.assert_called_once()

    @patch('auth_app.signals.send_email')
    def test_password_reset_for_non_existing_user(self, mock_send_email):
        """
        Checks that no email is sent for a non-existing user.
        """
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_not_called()

    def test_password_reset_invalid_email_format(self):
        """
        Ensures invalid email formats return a 400 response.
        """
        data = {'email': 'not-an-email'}
        response = self.client.post(self.reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class PasswordResetConfirmTests(APITestCase):
    """
    Tests password reset confirmation, token validation, and password rules.
    """
    def setUp(self):
        """
        Sets up a test user, token, UID, and confirmation URL.
        """
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="OldPassword123"
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.confirm_url = reverse(
            'password-reset-confirm',
            kwargs={'uidb64': self.uid, 'token': self.token}
        )

    def test_password_reset_confirm_success(self):
        """
        Confirms that a valid password reset succeeds and updates the password.
        """
        data = {'new_password': 'NewPassword123', 'confirm_password': 'NewPassword123'}
        response = self.client.post(self.confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123'))

    def test_password_reset_confirm_password_mismatch(self):
        """
        Validates that mismatched passwords return a 400 error.
        """
        data = {'new_password': 'NewPassword123', 'confirm_password': 'Mismatch123'}
        response = self.client.post(self.confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    def test_password_reset_confirm_invalid_token(self):
        """
        Ensures an invalid token prevents password reset and returns 400.
        """
        url = reverse(
            'password-reset-confirm',
            kwargs={'uidb64': self.uid, 'token': 'invalid-token'}
        )
        data = {'new_password': 'NewPassword123', 'confirm_password': 'NewPassword123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_password_reset_confirm_invalid_uid(self):
        """
        Ensures an invalid UID prevents password reset and returns 400.
        """
        url = reverse(
            'password-reset-confirm',
            kwargs={'uidb64': 'invaliduid', 'token': self.token}
        )
        data = {'new_password': 'NewPassword123', 'confirm_password': 'NewPassword123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_password_reset_confirm_too_short_password(self):
        """
        Checks that passwords shorter than 8 characters are rejected.
        """
        data = {'new_password': 'short', 'confirm_password': 'short'}
        response = self.client.post(self.confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)