from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from users.models import User


def create_notification(recipient_roles=None, assigned_users=None, specific_users=None, 
                        title="", message="", related_object=None, severity='MEDIUM',
                        notification_type=''):
    """
    Create notifications for multiple users based on roles, assignments, or specific users.
    
    Args:
        recipient_roles: List of role names (e.g., ['MANAGER', 'TECHNICIAN'])
        assigned_users: QuerySet of users assigned to a machine
        specific_users: List of specific User objects
        title: Notification title
        message: Notification message
        related_object: Associated object (e.g., Warning, Fault)
        severity: Notification severity ('LOW', 'MEDIUM', 'HIGH')
        notification_type: Type of notification from NOTIFICATION_TYPES
    
    Returns:
        List of created Notification objects
    """
    from notifications.models import Notification, NotificationPreference
    
    # Collect all recipient users without duplicates
    recipients = set()
    
    # Add users based on roles
    if recipient_roles:
        role_users = User.objects.filter(role__in=recipient_roles)
        recipients.update(role_users)
    
    # Add assigned users
    if assigned_users:
        recipients.update(assigned_users)
    
    # Add specific users
    if specific_users:
        recipients.update(specific_users)
    
    # Create notifications
    created_notifications = []
    
    for user in recipients:
        # Check user preferences
        preference = NotificationPreference.objects.filter(
            user=user,
            notification_type=notification_type
        ).first()
        
        # Default to sending in-app notification if no preference exists
        should_notify_in_app = True
        should_notify_email = False
        
        if preference:
            should_notify_in_app = preference.in_app
            should_notify_email = preference.email
        
        # Create in-app notification if enabled
        if should_notify_in_app:
            notification = Notification(
                recipient=user,
                title=title,
                message=message,
                notification_type=notification_type,
                severity=severity
            )
            
            # Set related object if provided
            if related_object:
                content_type = ContentType.objects.get_for_model(related_object)
                notification.content_type = content_type
                notification.object_id = related_object.id
            
            notification.save()
            created_notifications.append(notification)
            
            # Queue email notification if enabled
            if should_notify_email:
                from notifications.tasks import send_notification_email
                send_notification_email.delay(notification.id)
    
    return created_notifications


def get_unread_notifications(user):
    """
    Get all unread notifications for a user.
    """
    from notifications.models import Notification
    return Notification.objects.filter(recipient=user, read=False).order_by('-created_at')


def get_notifications_by_type(user, notification_type):
    """
    Get notifications for a user filtered by type.
    """
    from notifications.models import Notification
    return Notification.objects.filter(
        recipient=user,
        notification_type=notification_type
    ).order_by('-created_at')


def mark_all_as_read(user):
    """
    Mark all notifications as read for a user.
    """
    from notifications.models import Notification
    now = timezone.now()
    return Notification.objects.filter(
        recipient=user,
        read=False
    ).update(read=True, read_at=now)


def get_or_create_preferences(user):
    """
    Get or create notification preferences for a user.
    Ensures all notification types have a preference entry.
    """
    from notifications.models import NotificationPreference, Notification
    
    # Get existing preferences
    existing_prefs = NotificationPreference.objects.filter(user=user)
    existing_types = [pref.notification_type for pref in existing_prefs]
    
    # Create missing preferences with defaults
    for notification_type, _ in Notification.NOTIFICATION_TYPES:
        if notification_type not in existing_types:
            NotificationPreference.objects.create(
                user=user,
                notification_type=notification_type,
                in_app=True,
                email=True
            )
    
    # Return all preferences
    return NotificationPreference.objects.filter(user=user)