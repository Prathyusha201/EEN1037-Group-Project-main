"""
Signal handlers for Machine models.
"""
from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Machine, StatusChange, MachineCollection
from notifications.utils import send_notification


@receiver(post_save, sender=Machine)
def machine_created_handler(sender, instance, created, **kwargs):
    """
    Signal handler for when a new machine is created.
    Sends notifications and creates an initial status entry.
    """
    if created:
        # Create initial status history entry
        StatusChange.objects.create(
            machine=instance,
            previous_status=Machine.STATUS_OK,
            new_status=Machine.STATUS_OK,
            changed_by=instance.created_by,
            reason="Initial machine creation"
        )
        
        # Notify managers about new machine
        from django.contrib.auth import get_user_model
        User = get_user_model()
        managers = User.objects.filter(role='Manager')
        
        for manager in managers:
            send_notification(
                recipient=manager,
                title=f"New Machine Added: {instance.name}",
                message=f"A new machine has been added to the system: {instance.name} ({instance.model_number})",
                related_object=instance,
                notification_type='machine_created'
            )


@receiver(m2m_changed, sender=Machine.assigned_technicians.through)
def technician_assignment_changed(sender, instance, action, pk_set, **kwargs):
    """
    Signal handler for when technicians are assigned to or removed from a machine.
    Sends notifications to the affected technicians.
    """
    if action not in ('post_add', 'post_remove'):
        return
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if action == 'post_add' and pk_set:
        # Notify newly assigned technicians
        technicians = User.objects.filter(pk__in=pk_set)
        for tech in technicians:
            send_notification(
                recipient=tech,
                title=f"New Machine Assignment: {instance.name}",
                message=f"You have been assigned to machine: {instance.name} ({instance.model_number})",
                related_object=instance,
                notification_type='assignment'
            )
    
    elif action == 'post_remove' and pk_set:
        # Notify technicians who were removed from assignment
        technicians = User.objects.filter(pk__in=pk_set)
        for tech in technicians:
            send_notification(
                recipient=tech,
                title=f"Machine Assignment Removed: {instance.name}",
                message=f"You have been unassigned from machine: {instance.name} ({instance.model_number})",
                related_object=instance,
                notification_type='unassignment'
            )


@receiver(m2m_changed, sender=Machine.assigned_repair.through)
def repair_assignment_changed(sender, instance, action, pk_set, **kwargs):
    """
    Signal handler for when repair personnel are assigned to or removed from a machine.
    Sends notifications to the affected repair personnel.
    """
    if action not in ('post_add', 'post_remove'):
        return
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if action == 'post_add' and pk_set:
        # Notify newly assigned repair personnel
        repair_staff = User.objects.filter(pk__in=pk_set)
        for staff in repair_staff:
            send_notification(
                recipient=staff,
                title=f"New Machine Assignment: {instance.name}",
                message=f"You have been assigned to machine: {instance.name} ({instance.model_number})",
                related_object=instance,
                notification_type='assignment'
            )
    
    elif action == 'post_remove' and pk_set:
        # Notify repair personnel who were removed from assignment
        repair_staff = User.objects.filter(pk__in=pk_set)
        for staff in repair_staff:
            send_notification(
                recipient=staff,
                title=f"Machine Assignment Removed: {instance.name}",
                message=f"You have been unassigned from machine: {instance.name} ({instance.model_number})",
                related_object=instance,
                notification_type='unassignment'
            )


@receiver(pre_delete, sender=Machine)
def machine_deleted_handler(sender, instance, **kwargs):
    """
    Signal handler for when a machine is deleted.
    Sends notifications to assigned personnel and managers.
    """
    # Collect all users to notify
    users_to_notify = set()
    users_to_notify.update(instance.assigned_technicians.all())
    users_to_notify.update(instance.assigned_repair.all())
    
    # Add managers
    from django.contrib.auth import get_user_model
    User = get_user_model()
    managers = User.objects.filter(role='Manager')
    users_to_notify.update(managers)
    
    # Send notifications
    for user in users_to_notify:
        send_notification(
            recipient=user,
            title=f"Machine Deleted: {instance.name}",
            message=f"Machine {instance.name} ({instance.model_number}) has been removed from the system",
            notification_type='machine_deleted'
        )