from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserPreference, UserMachineAssignment

class UserPreferenceInline(admin.StackedInline):
    model = UserPreference
    can_delete = False
    verbose_name_plural = 'preferences'

class UserAdmin(BaseUserAdmin):
    """Custom admin view for the User model."""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Role and permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_activity', 'last_password_change')}),
        (_('Profile'), {'fields': ('phone_number', 'department', 'profile_image')}),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'last_activity', 'last_password_change')
    inlines = (UserPreferenceInline,)
    
    def save_model(self, request, obj, form, change):
        """Save model and create default preferences if needed."""
        super().save_model(request, obj, form, change)
        UserPreference.objects.get_or_create(user=obj)


@admin.register(UserMachineAssignment)
class UserMachineAssignmentAdmin(admin.ModelAdmin):
    """Admin view for user-machine assignments."""
    list_display = ('user', 'machine', 'assigned_date', 'assigned_by')
    list_filter = ('assigned_date', 'assigned_by')
    search_fields = ('user__username', 'machine__name')
    date_hierarchy = 'assigned_date'
    raw_id_fields = ('user', 'machine', 'assigned_by')


# Register models
admin.site.register(User, UserAdmin)