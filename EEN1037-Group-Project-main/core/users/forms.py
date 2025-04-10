from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserLoginForm(AuthenticationForm):
    """Custom login form with remember me functionality."""
    
    remember_me = forms.BooleanField(required=False, initial=False, 
                                     widget=forms.CheckboxInput())
    
    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['remember_me'].widget.attrs.update({'class': 'form-check-input'})


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users by managers."""
    
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone_number')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with that email already exists."))
        return email


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email'})


class CustomSetPasswordForm(SetPasswordForm):
    """Custom form for setting a new password."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})


class UserPreferenceForm(forms.ModelForm):
    """Form for updating user preferences."""
    
    class Meta:
        from .models import UserPreference
        model = UserPreference
        exclude = ('user',)
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_case_assignment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_case_update': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_case_resolution': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_machine_status_change': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_warning_created': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'items_per_page': forms.NumberInput(attrs={'class': 'form-control'}),
            'default_dashboard_view': forms.Select(attrs={'class': 'form-select'}),
        }