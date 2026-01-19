from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """
    Authentication class that extracts a JWT access token from cookies and
    injects it into the `Authorization` header for standard JWT processing.
    """
    def authenticate(self, request):
        """
        Retrieves the `access_token` from cookies; returns `None` if absent.
        If present, adds it as a `Bearer` token to the `Authorization` header
        and proceeds with the parent JWT authentication logic.
        """
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None

        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        return super().authenticate(request)
    
class IsOwner(BasePermission):
    """
    Permission class that grants access only if the requesting user
    is the owner of the given object.
    """
    def has_object_permission(self, request, view, obj):
        """
        Returns `True` if the authenticated user matches `obj.owner`,
        otherwise denies access.
        """
        return request.user == obj.owner