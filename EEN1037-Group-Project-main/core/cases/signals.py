"""
Signal handlers for case-related events.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from cases.models import Case, CaseStatusChange, CaseAssignmentHistory, CaseStatus
from notifications.utils import create_notification

@receiver(post_save, sender=Case)
def case_created_handler(sender, instance, created, **kwargs):
    """
    Handle case creation events - set machine to fault status,
    create notification for relevant users.
    """
    if created:
        # Set machine status to fault when a case is created
        machine = instance.machine
        machine.status = 'FAULT'  # Import MachineStatus if not using string literals
        machine.save()
        
        # Create notification for new case
        notification_users = []
        
        # Add assigned user if applicable
        if instance.assigned_to:
            notification_users.append(instance.assigned_to)
        
        # Add users assigned to the machine
        notification_users.extend(machine.assigned_users.all())
        
        # Add all managers
        from users.models import User
        from django.contrib.auth.models import Group
        manager_group = Group.objects.get(name='Manager')
        managers = User.objects.filter(groups=manager_group)
        notification_users.extend(managers)
        
        # Create unique notifications for each user
        for user in set(notification_users):
            create_notification(
                user=user,
                title=f"New Case Created: {instance.case_number}",
                message=f"A new case has been created for {machine.name}",
                link=f"/cases/{instance.id}/",
                notification_type='NEW_CASE'
            )

@receiver(pre_save, sender=Case)
def case_status_change_detector(sender, instance, **kwargs):
    """
    Detect case status changes for proper handling.
    """
    if instance.pk:
        try:
            old_instance = Case.objects.get(pk=instance.pk)
            # Store original status for signal handlers
            instance._original_status = old_instance.status
            # Store original assigned_to for assignment tracking
            instance._original_assigned_to = old_instance.assigned_to
        except Case.DoesNotExist:
            pass

@receiver(post_save, sender=Case)
def case_status_change_handler(sender, instance, created, **kwargs):
    """
    Handle case status changes - update machine status if needed,
    create notification for relevant users.
    """
    if not created and hasattr(instance, '_original_status'):
        if instance._original_status != instance.status:
            # Status has changed - create notification
            notification_title = f"Case Status Changed: {instance.case_number}"
            notification_message = f"Case status changed from {instance._original_status} to {instance.status}"
            
            # Create notification for relevant users
            notification_users = [
                instance.created_by,
                instance.assigned_to,
            ]
            
            # Add machine's assigned users
            notification_users.extend(instance.machine.assigned_users.all())
            
            # Create unique notifications
            for user in set(filter(None, notification_users)):
                create_notification(
                    user=user,
                    title=notification_title,
                    message=notification_message,
                    link=f"/cases/{instance.id}/",
                    notification_type='STATUS_CHANGE'
                )
                
            # If case is resolved, update machine status
            if instance.status == CaseStatus.RESOLVED:
                instance.machine.check_status_after_case_resolution()

@receiver(post_save, sender=Case)
def case_assignment_change_handler(sender, instance, created, **kwargs):
    """
    Track case assignment changes and create relevant notifications.
    """
    if not created and hasattr(instance, '_original_assigned_to'):
        if instance._original_assigned_to != instance.assigned_to:
            # Assignment has changed - track history
            CaseAssignmentHistory.objects.create(
                case=instance,
                assigned_from=instance._original_assigned_to,
                assigned_to=instance.assigned_to,
                assigned_by=instance._current_user if hasattr(instance, '_current_user') else None
            )
            
            # Create notification for new assignee
            if instance.assigned_to:
                create_notification(
                    user=instance.assigned_to,
                    title=f"Case Assigned: {instance.case_number}",
                    message=f"You have been assigned to case {instance.case_number}",
                    link=f"/cases/{instance.id}/",
                    notification_type='ASSIGNMENT'
                )