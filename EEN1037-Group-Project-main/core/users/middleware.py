from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
import datetime
from django.contrib.auth import logout
from django.contrib import messages
import re


class RoleBasedAccessMiddleware:
    """Middleware for role-based access control."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Compile URL patterns for different roles
        self.manager_only_patterns = [
            re.compile(r'^/users/list/'),
            re.compile(r'^/users/create/'),
            re.compile(r'^/users/update/'),
            re.compile(r'^/machines/create/'),
            re.compile(r'^/machines/delete/'),
            re.compile(r'^/collections/'),
            re.compile(r'^/reports/'),
            re.compile(r'^/api/admin/')
        ]
        
        self.repair_patterns = [
            re.compile(r'^/cases/resolve/'),
            re.compile(r'^/warnings/delete/'),
            re.compile(r'^/api/cases/resolve/')
        ]
        
        self.technician_patterns = [
            re.compile(r'^/cases/create/'),
            re.compile(r'^/warnings/create/'),
            re.compile(r'^/api/cases/create/'),
            re.compile(r'^/api/warnings/create/')
        ]
        
        # Public URLs that don't require authentication
        self.public_patterns = [
            re.compile(r'^/users/login/'),
            re.compile(r'^/users/password/reset/'),
            re.compile(r'^/static/'),
            re.compile(r'^/media/'),
            re.compile(r'^/api/public/'),
            re.compile(r'^/favicon.ico')
        ]
    
    def __call__(self, request):
        # Check if URL requires authentication
        path = request.path
        
        # Allow public URLs without authentication
        for pattern in self.public_patterns:
            if pattern.match(path):
                return self.get_response(request)
        
        # If not authenticated, redirect to login
        if not request.user.is_authenticated:
            # If API request, return 401
            if path.startswith('/api/'):
                from django.http import JsonResponse
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            return redirect(f"{reverse('users:login')}?next={request.path}")
        
        # Handle restricted URLs based on user role
        restricted = False
        
        # Check manager-only URLs
        for pattern in self.manager_only_patterns:
            if pattern.match(path) and not request.user.is_manager():
                restricted = True
                break
        
        # Check repair-only URLs
        for pattern in self.repair_patterns:
            if pattern.match(path) and not (request.user.is_repair() or request.user.is_manager()):
                restricted = True
                break
        
        # Check technician-only URLs
        for pattern in self.technician_patterns:
            if pattern.match(path) and (
                not request.user.is_technician() and 
                not request.user.is_repair() and 
                not request.user.is_manager()
            ):
                restricted = True
                break
        
        if restricted:
            # If API request, return 403
            if path.startswith('/api/'):
                from django.http import JsonResponse
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # For web request, redirect with message
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard:index')
        
        # Update last activity timestamp
        if request.user.is_authenticated:
            request.user.update_last_activity()
        
        response = self.get_response(request)
        return response


class SessionTimeoutMiddleware:
    """Middleware for handling session timeouts."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = timezone.now()
            
            # Get last activity time
            last_activity = request.user.last_activity
            
            # If last_activity is None, set it to current time
            if not last_activity:
                request.user.update_last_activity()
            else:
                # Check session timeout (default 24 hours from settings)
                timeout = getattr(settings, 'SESSION_TIMEOUT', 86400)  # Default 24 hours
                
                # Calculate time difference
                time_diff = current_time - last_activity
                
                # Check if session has timed out
                if time_diff.total_seconds() > timeout:
                    # Logout user
                    logout(request)
                    
                    # If API request, return 401
                    if request.path.startswith('/api/'):
                        from django.http import JsonResponse
                        return JsonResponse({'error': 'Session expired'}, status=401)
                    
                    # For web request, redirect to login with message
                    messages.info(request, "Your session has expired. Please log in again.")
                    return redirect(settings.LOGIN_URL)
                
                from django.contrib.auth.hashers import check_password
                # Check for remember token
                if 'remember_token' in request.COOKIES:
                    token = request.COOKIES.get('remember_token')
                    # Try to find user with this token
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    try:
                        user = User.objects.get(remember_token_expires__gt=current_time)
                        if check_password(token, user.remember_token):
                            from django.contrib.auth import login
                            login(request, user)
                            # Update last activity
                            user.update_last_activity()
                            
                    except User.DoesNotExist:
                        # Invalid token, remove cookie
                        response = self.get_response(request)
                        response.delete_cookie('remember_token')
                        return response
        
        response = self.get_response(request)
        return response