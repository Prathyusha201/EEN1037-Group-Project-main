from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import UserMachineAssignment
import random
import string

User = get_user_model()


def get_user_by_email(email):
    """Get user by email address."""
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


def get_user_role_display(user):
    """Get user role display name."""
    return dict(User.ROLE_CHOICES).get(user.role, "Unknown")


def get_users_by_role(role):
    """Get all users with a specific role."""
    return User.objects.filter(role=role)


def get_active_users():
    """Get all active users."""
    return User.objects.filter(is_active=True)


def generate_temp_password(length=10):
    """Generate a temporary password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


def send_account_created_email(user, temp_password=None):
    """Send account created email to user."""
    subject = 'Your ACME Manufacturing Account'
    context = {
        'user': user,
        'temp_password': temp_password,
        'login_url': f"{settings.BASE_URL}{settings.LOGIN_URL}"
    }
    
    html_message = render_to_string('users/email_templates/account_created.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False
    )


def get_assigned_machines(user):
    """Get all machines assigned to user."""
    assignments = UserMachineAssignment.objects.filter(user=user)
    return [assignment.machine for assignment in assignments]


def get_assigned_users(machine):
    """Get all users assigned to machine."""
    assignments = UserMachineAssignment.objects.filter(machine=machine)
    return [assignment.user for assignment in assignments]


def assign_user_to_machine(user, machine, assigned_by=None):
    """Assign user to machine."""
    # Check if assignment already exists
    if UserMachineAssignment.objects.filter(user=user, machine=machine).exists():
        return False
    
    # Create new assignment
    UserMachineAssignment.objects.create(
        user=user,
        machine=machine,
        assigned_by=assigned_by
    )
    
    return True


def unassign_user_from_machine(user, machine):
    """Unassign user from machine."""
    try:
        assignment = UserMachineAssignment.objects.get(user=user, machine=machine)
        assignment.delete()
        return True
    except UserMachineAssignment.DoesNotExist:
        return False


def get_technician_teams():
    """Get teams of technicians for UI display."""
    technicians = User.objects.filter(role=User.TECHNICIAN, is_active=True)
    teams = {}
    
    for tech in technicians:
        department = tech.department or "Unassigned"
        if department not in teams:
            teams[department] = []
        
        teams[department].append(tech)
    
    return teams


def get_repair_teams():
    """Get teams of repair staff for UI display."""
    repair_staff = User.objects.filter(role=User.REPAIR, is_active=True)
    teams = {}
    
    for staff in repair_staff:
        department = staff.department or "Unassigned"
        if department not in teams:
            teams[department] = []
        
        teams[department].append(staff)
    
    return teams