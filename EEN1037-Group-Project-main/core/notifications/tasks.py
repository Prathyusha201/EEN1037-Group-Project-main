from django.utils import timezone
from django.db.models import Q

# Define task decorator - if using Celery
try:
    from celery import shared_task
except ImportError:
    # Define a dummy decorator if Celery is not available
    def shared_task(func):
        return func


@shared_task
def send_notification_email(notification_id):
    """
    Task to send an email for a notification.
    """
    from notifications.models import Notification
    from notifications.email import send_notification_email_to_user
    
    try:
        notification = Notification.objects.get(id=notification_id)
        return send_notification_email_to_user(notification)
    except Notification.DoesNotExist:
        return False


@shared_task
def send_pending_notification_emails():
    """
    Task to send all pending notification emails.
    This can be scheduled to run periodically to batch emails.
    """
    from notifications.models import Notification
    from notifications.email import send_notification_email_to_user
    
    # Get all notifications where email should be sent but hasn't been yet
    pending_notifications = Notification.objects.filter(
        email_sent=False
    ).select_related('recipient')
    
    success_count = 0
    failure_count = 0
    
    for notification in pending_notifications:
        if send_notification_email_to_user(notification):
            success_count += 1
        else:
            failure_count += 1
    
    return {
        'success': success_count,
        'failure': failure_count,
        'total': success_count + failure_count
    }


@shared_task
def clean_old_notifications(days=30):
    """
    Task to clean up old read notifications.
    """
    from notifications.models import Notification
    
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Delete old read notifications
    old_notifications = Notification.objects.filter(
        Q(read=True) & Q(created_at__lt=cutoff_date)
    )
    
    count, _ = old_notifications.delete()
    
    return {
        'deleted_count': count,
        'cutoff_date': cutoff_date.isoformat()
    }