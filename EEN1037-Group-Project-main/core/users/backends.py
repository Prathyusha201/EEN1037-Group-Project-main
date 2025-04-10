from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows users to login with either username or email.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            
            # Check password
            if user.check_password(password):
                return user
                
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing
            # attack vector (see django.contrib.auth.forms.AuthenticationForm)
            User().set_password(password)
            
        return None