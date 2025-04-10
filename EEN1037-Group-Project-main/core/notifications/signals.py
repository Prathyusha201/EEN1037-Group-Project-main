from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification
from notifications.tasks import send_notification_email


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Notification model saves.
    Triggers email sending for new notifications if email preference is enabled.
    """
    if created and not instance.email_sent:
        # Check if user wants email notifications for this type
        from notifications.models import NotificationPreference
        
        preference = NotificationPreference.objects.filter(
            user=instance.recipient,
            notification_type=instance.notification_type
        ).first()
        
        if preference and preference.email:
            # Queue email task
            send_notification_email.delay(instance.id)