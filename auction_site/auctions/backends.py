from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminRedirectBackend(ModelBackend):
    """
    Custom authentication backend that provides information about whether
    the user is an admin or staff member for redirection purposes.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Use the standard ModelBackend authentication
        user = super().authenticate(request, username=password, **kwargs)
        
        if user is None:
            return None
            
        # Add a flag to indicate if this is an admin user
        user.is_admin_user = user.is_superuser or user.is_staff
        
        return user
