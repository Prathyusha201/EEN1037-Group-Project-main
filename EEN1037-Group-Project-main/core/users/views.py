from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, 
    PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, JsonResponse

from .forms import (
    UserLoginForm, CustomUserCreationForm, CustomPasswordResetForm, 
    CustomSetPasswordForm, UserPreferenceForm
)
from .models import User, UserPreference, UserMachineAssignment
from .permissions import manager_required, is_manager, is_technician, is_repair_staff

import datetime
import uuid

class CustomLoginView(LoginView):
    """Custom login view with remember me functionality."""
    
    form_class = UserLoginForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Handle valid form - implement remember me functionality."""
        # Call parent class's form_valid to authenticate user
        response = super().form_valid(form)
        
        # Get the remember_me data from the form
        remember_me = form.cleaned_data.get('remember_me', False)
        
        if remember_me:
            # Set session expiry to 30 days
            self.request.session.set_expiry(30 * 24 * 60 * 60)
            
            # Generate a remember token
            token = str(uuid.uuid4())
            expires = timezone.now() + datetime.timedelta(days=30)
            
            # Save token to user
            user = form.get_user()
            user.remember_token = token
            user.remember_token_expires = expires
            user.save(update_fields=['remember_token', 'remember_token_expires'])
            
            # Set cookie
            response.set_cookie('remember_token', token, max_age=30 * 24 * 60 * 60, httponly=True, secure=True)
        else:
            # Default session length (set in settings)
            self.request.session.set_expiry(None)
        
        # Update last activity timestamp
        form.get_user().update_last_activity()
        
        return response


class CustomLogoutView(LogoutView):
    """Custom logout view that clears remember me token."""
    
    next_page = reverse_lazy('users:login')
    
    def dispatch(self, request, *args, **kwargs):
        """Clear remember me token on logout."""
        if request.user.is_authenticated:
            # Clear remember token
            request.user.remember_token = None
            request.user.remember_token_expires = None
            request.user.save(update_fields=['remember_token', 'remember_token_expires'])
            
            # Clear cookie
            response = super().dispatch(request, *args, **kwargs)
            response.delete_cookie('remember_token')
            return response
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view."""
    
    template_name = 'users/password_reset.html'
    email_template_name = 'users/email_templates/password_reset.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view."""
    
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view."""
    
    template_name = 'users/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('users:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view."""
    
    template_name = 'users/password_reset_complete.html'


@login_required
@manager_required
class UserListView(ListView):
    """View to display all users (managers only)."""
    
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        """Filter queryset based on search parameters."""
        queryset = super().get_queryset()
        
        # Apply filters
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Apply search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        
        return queryset


@login_required
@manager_required
class UserCreateView(CreateView):
    """View to create a new user (managers only)."""
    
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_create.html'
    success_url = reverse_lazy('users:user_list')
    
    def form_valid(self, form):
        """Save form and create default preferences."""
        # Create user
        user = form.save()
        
        # Create default preferences
        UserPreference.objects.create(user=user)
        
        messages.success(self.request, f"User {user.username} created successfully.")
        return super().form_valid(form)


@login_required
@manager_required
class UserUpdateView(UpdateView):
    """View to update a user (managers only)."""
    
    model = User
    template_name = 'users/user_update.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'department', 'phone_number']
    success_url = reverse_lazy('users:user_list')
    
    def form_valid(self, form):
        """Save form with success message."""
        user = form.save()
        messages.success(self.request, f"User {user.username} updated successfully.")
        return super().form_valid(form)


@login_required
def profile_view(request):
    """View for users to see and edit their own profile."""
    
    if request.method == 'POST':
        # Handle profile update
        user_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'phone_number': request.POST.get('phone_number'),
        }
        
        # Update user
        user = request.user
        for key, value in user_data.items():
            setattr(user, key, value)
        user.save()
        
        # Update preferences
        preference = user.preferences
        preference.email_notifications = 'email_notifications' in request.POST
        preference.in_app_notifications = 'in_app_notifications' in request.POST
        preference.notify_on_case_assignment = 'notify_on_case_assignment' in request.POST
        preference.notify_on_case_update = 'notify_on_case_update' in request.POST
        preference.notify_on_case_resolution = 'notify_on_case_resolution' in request.POST
        preference.notify_on_machine_status_change = 'notify_on_machine_status_change' in request.POST
        preference.notify_on_warning_created = 'notify_on_warning_created' in request.POST
        preference.items_per_page = int(request.POST.get('items_per_page', 25))
        preference.default_dashboard_view = request.POST.get('default_dashboard_view', 'assigned')
        preference.save()
        
        # Handle profile image upload
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            user.save()
        
        messages.success(request, "Profile updated successfully.")
        return redirect('users:profile')
    
    return render(request, 'users/profile.html', {
        'user': request.user,
        'preferences': request.user.preferences,
    })


@login_required
def change_password(request):
    """View for users to change their password."""
    
    if request.method == 'POST':
        # Verify current password
        current_password = request.POST.get('current_password')
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect('users:change_password')
        
        # Check if new passwords match
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect('users:change_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session auth hash to keep user logged in
        update_session_auth_hash(request, request.user)
        
        messages.success(request, "Password changed successfully.")
        return redirect('users:profile')
    
    return render(request, 'users/change_password.html')