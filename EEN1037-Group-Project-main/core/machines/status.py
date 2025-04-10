"""
Status management system for machines.
This module contains utilities for handling machine status transitions,
validation, and notifications for status changes.
"""
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction

from notifications.utils import send_notification


class MachineStatusManager:
    """Manager class for handling machine status transitions and validations."""
    
    @staticmethod
    def validate_status_transition(machine, new_status, user=None):
        """
        Validates if a status transition is allowed.
        
        Args:
            machine: The machine instance to validate
            new_status: The requested new status
            user: The user requesting the status change
            
        Returns:
            bool: True if the transition is valid
            
        Raises:
            ValidationError: If the transition is invalid
        """
        current_status = machine.current_status
        
        # Cannot transition to the same status
        if current_status == new_status:
            raise ValidationError(f"Machine is already in {new_status} status")
        
        if current_status == machine.STATUS_OK and new_status == machine.STATUS_WARNING and user.role != 'Technician':
            raise ValidationError("Only technicians can mark a machine as 'Warning'")
            
        # Only repair personnel can resolve faults (transition from FAULT to OK)
        if (current_status == machine.STATUS_FAULT and 
            new_status == machine.STATUS_OK and 
            user and user.role != 'Repair'):
            raise ValidationError("Only repair personnel can resolve faults")
            
        return True
    
    @staticmethod
    @transaction.atomic
    def change_status(machine, new_status, user=None, reason=None):
        """
        Changes the status of a machine and records the change.
        
        Args:
            machine: The machine instance to update
            new_status: The new status to set
            user: The user making the status change
            reason: The reason for the status change
            
        Returns:
            StatusChange: The created status change record
        """
        from machines.models import StatusChange
        
        current_status = machine.current_status
        
        # Validate the transition
        MachineStatusManager.validate_status_transition(machine, new_status, user)
        
        # Create a status change record
        status_change = StatusChange.objects.create(
            machine=machine,
            previous_status=current_status,
            new_status=new_status,
            changed_by=user,
            reason=reason or ""
        )
        
        # Send notifications to relevant users
        MachineStatusManager._notify_status_change(machine, status_change)
        
        return status_change
    
    @staticmethod
    def _notify_status_change(machine, status_change):
        """
        Sends notifications to relevant users about a status change.
        
        Args:
            machine: The machine that had a status change
            status_change: The status change record
        """
        # Determine recipients based on machine assignments
        recipients = set()
        recipients.update(machine.assigned_technicians.all())
        recipients.update(machine.assigned_repair.all())
        
        # Add managers to the recipients
        from django.contrib.auth import get_user_model
        User = get_user_model()
        managers = User.objects.filter(role='Manager')
        recipients.update(managers)
        
        # Create and send notification
        title = f"Status Change: {machine.name}"
        message = (f"Status changed from {status_change.previous_status} to "
                   f"{status_change.new_status}. {status_change.reason}")
        
        for recipient in recipients:
            send_notification(
                recipient=recipient,
                title=title,
                message=message,
                related_object=machine,
                notification_type='status_change'
            )


def get_aggregate_status(machines):
    """
    Calculates the aggregate status for a collection of machines.
    Returns the most severe status among all machines.
    
    Args:
        machines: A queryset of Machine instances
        
    Returns:
        str: The aggregate status (OK, Warning, or Fault)
    """
    from machines.models import Machine
    
    status_severity = {
        Machine.STATUS_OK: 0,
        Machine.STATUS_WARNING: 1,
        Machine.STATUS_FAULT: 2
    }
    
    highest_severity = -1
    highest_status = Machine.STATUS_OK
    
    for machine in machines:
        current_status = machine.current_status
        severity = status_severity.get(current_status, 0)
        
        if severity > highest_severity:
            highest_severity = severity
            highest_status = current_status
    
    return highest_status