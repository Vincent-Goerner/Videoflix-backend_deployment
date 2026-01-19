import os
from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import Signal, receiver
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


user_registered = Signal()
password_reset = Signal()
frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")


def send_email(subject, text, template, context, recipient):
    """
    Send an email with optional HTML content rendered from a template.
    Wraps Django's send_mail and logs errors on failure.
    """
    try:
        send_mail(
            subject,
            text,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            html_message=render_to_string(template, context),
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email sending failed: {e}")


@receiver(user_registered)
def send_activation_email(sender, user, token, **kwargs):
    """
    Send an account activation email after user registration.
    Generates a UID/token-based activation link for the frontend.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    link = (
        f"{frontend_url}/pages/auth/activate.html"
        f"?uid={uidb64}&token={token}"
    )

    send_email(
        'Activate Your Videoflix Account',
        f'Please activate your account by visiting: {link}',
        'activation_mail.html',
        {'user_name': user.email, 'activation_link': link},
        user.email,
    )


@receiver(password_reset)
def send_password_reset_email(sender, user, token, **kwargs):
    """
    Send a password reset email with a time-limited reset link.
    Uses Django settings to determine link validity duration.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    link = (
        f"{frontend_url}/pages/auth/confirm_password.html"
        f"?uid={uidb64}&token={token}"
    )

    send_email(
        'Reset Your Videoflix Password',
        f'Please reset your password by visiting: {link}',
        'password_reset_mail.html',
        {'reset_link': link},
        user.email,
    )