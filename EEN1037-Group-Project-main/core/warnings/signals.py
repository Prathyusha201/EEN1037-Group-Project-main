from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from warnings.models import Warning
from notifications.utils import create_notification


@receiver(post_save, sender=Warning)
def warning_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Warning model saves.
    Creates notifications when warnings are created or resolved.
    """
    if created:
        # Create notification for new warning
        create_notification(
            recipient_roles=['TECHNICIAN', 'REPAIR', 'MANAGER'],
            assigned_users=instance.machine.assigned_users.all(),
            title=f"New Warning: {instance.machine.name}",
            message=f"Warning: {instance.text}",
            related_object=instance,
            severity=instance.severity,
            notification_type='WARNING_CREATED'
        )
    elif not instance.active and instance.resolved_at:
        # Create notification for resolved warning
        create_notification(
            recipient_roles=['TECHNICIAN', 'REPAIR', 'MANAGER'],
            assigned_users=instance.machine.assigned_users.all(),
            title=f"Warning Resolved: {instance.machine.name}",
            message=f"Warning resolved: {instance.text}",
            related_object=instance,
            severity='LOW',
            notification_type='WARNING_RESOLVED'
        )