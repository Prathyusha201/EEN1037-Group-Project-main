from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Custom manager for User model with additional methods."""
    
    def create_user(self, email, username, password=None, **extra_fields):
        """Create and save a regular User with the given email, username, and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and save a SuperUser with the given email, username, and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.MANAGER)
        
        return self.create_user(email, username, password, **extra_fields)
    
    def technicians(self):
        """Return queryset of all technician users."""
        return self.filter(role=User.TECHNICIAN)
    
    def repair_staff(self):
        """Return queryset of all repair staff users."""
        return self.filter(role=User.REPAIR)
    
    def managers(self):
        """Return queryset of all manager users."""
        return self.filter(role=User.MANAGER)
    
    def view_only(self):
        """Return queryset of all view-only users."""
        return self.filter(role=User.VIEW_ONLY)


class User(AbstractUser):
    """Custom User model with role-based permissions."""
    
    # Role choices
    TECHNICIAN = 'technician'
    REPAIR = 'repair'
    MANAGER = 'manager'
    VIEW_ONLY = 'view_only'
    
    ROLE_CHOICES = [
        (TECHNICIAN, _('Technician')),
        (REPAIR, _('Repair Personnel')),
        (MANAGER, _('Manager')),
        (VIEW_ONLY, _('View Only')),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    from django.contrib.auth.models import Group

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=VIEW_ONLY)

    def assign_group(self):
        """Assign Django group based on role"""
        group, _ = group.objects.get_or_create(name=self.role)
        self.groups.set([group])
        self.save()

    last_activity = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(auto_now_add=True)
    
    # Profile fields
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    # Remember me token
    remember_token = models.CharField(max_length=255, blank=True, null=True)
    remember_token_expires = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            self.assign_group()
    
    def update_last_activity(self):
        """Update the last activity timestamp for the user."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    # Role-based permission methods
    def is_technician(self):
        """Check if user is a technician."""
        return self.role == self.TECHNICIAN
    
    def is_repair(self):
        """Check if user is repair personnel."""
        return self.role == self.REPAIR
    
    def is_manager(self):
        """Check if user is a manager."""
        return self.role == self.MANAGER
    
    def is_view_only(self):
        """Check if user has view-only permissions."""
        return self.role == self.VIEW_ONLY
    

class UserPreference(models.Model):
    """Model to store user preferences for notifications and UI."""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    
    # Notification types
    notify_on_case_assignment = models.BooleanField(default=True)
    notify_on_case_update = models.BooleanField(default=True)
    notify_on_case_resolution = models.BooleanField(default=True)
    notify_on_machine_status_change = models.BooleanField(default=True)
    notify_on_warning_created = models.BooleanField(default=True)
    
    # UI preferences
    items_per_page = models.IntegerField(default=25)
    default_dashboard_view = models.CharField(max_length=20, default='assigned')
    
    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class UserMachineAssignment(models.Model):
    """Model to track which users are assigned to which machines."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='machine_assignments')
    machine = models.ForeignKey('machines.Machine', on_delete=models.CASCADE, related_name='assigned_users')
    assigned_date = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='machine_assignments_made'
    )
    
    class Meta:
        unique_together = ('user', 'machine')
        verbose_name = "User-Machine Assignment"
        verbose_name_plural = "User-Machine Assignments"
    
    def __str__(self):
        return f"{self.user.username} assigned to {self.machine.name}"