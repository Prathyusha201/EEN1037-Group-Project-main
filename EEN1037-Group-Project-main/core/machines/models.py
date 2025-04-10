from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

# Regex validator for collection names
collection_name_validator = RegexValidator(
    r'^[A-Za-z0-9\-]+$',
    message="Collection name can only contain letters, numbers, and hyphens."
)

class MachineCollection(models.Model):
    """
    A collection of machines - can be used for grouping machines by location, type, etc.
    Collections are flat and can only contain machines (no nested collections).
    """
    name = models.CharField(
        max_length=100, 
        validators=[collection_name_validator],
        unique=True
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Machine(models.Model):
    """
    Model representing a piece of machinery in the factory.
    A machine can have the status "OK", "Warning", or "Fault".
    """
    # Status choices - actual status is determined by the status system
    STATUS_OK = 'OK'
    STATUS_WARNING = 'Warning'
    STATUS_FAULT = 'Fault'
    
    name = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    installation_date = models.DateField()
    importance = models.PositiveIntegerField(
        default=0,
        help_text="Higher values indicate more important machinery (affects sorting)"
    )
    
    # Related fields
    collections = models.ManyToManyField(
        MachineCollection, 
        related_name='machines',
        blank=True
    )
    assigned_technicians = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_machines_tech',
        limit_choices_to={'role': 'Technician'},
        blank=True
    )
    assigned_repair = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_machines_repair',
        limit_choices_to={'role': 'Repair'},
        blank=True
    )
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_machines'
    )
    
    # Manager
    objects = models.Manager()
    
    def __str__(self):
        return f"{self.name} ({self.model_number})"
    
    @property
    def current_status(self):
        """
        Returns the current status of the machine based on active warnings and faults.
        If any fault cases are open, status is FAULT.
        If any warnings are active, status is WARNING.
        Otherwise, status is OK.
        """
        from cases.models import Case
        
        # Check for open fault cases
        open_faults = Case.objects.filter(
            machine=self,
            status__in=['open', 'in_progress']
        ).exists()
        
        if open_faults:
            return self.STATUS_FAULT
        
        # Check for active warnings
        active_warnings = self.warnings.filter(is_active=True).exists()
        
        if active_warnings:
            return self.STATUS_WARNING
        
        return self.STATUS_OK
    
    def get_active_warnings(self):
        """Returns all active warnings for this machine."""
        return self.warnings.filter(is_active=True)
    
    def get_open_cases(self):
        """Returns all open fault cases for this machine."""
        from cases.models import Case
        return Case.objects.filter(
            machine=self,
            status__in=['open', 'in_progress']
        )
    
    class Meta:
        ordering = ['-importance', 'name']


class StatusChange(models.Model):
    """
    Records a change in status for a machine.
    Used for historical tracking of status changes.
    """
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    previous_status = models.CharField(
        max_length=10,
        choices=[
            (Machine.STATUS_OK, 'OK'),
            (Machine.STATUS_WARNING, 'Warning'),
            (Machine.STATUS_FAULT, 'Fault'),
        ]
    )
    new_status = models.CharField(
        max_length=10,
        choices=[
            (Machine.STATUS_OK, 'OK'),
            (Machine.STATUS_WARNING, 'Warning'),
            (Machine.STATUS_FAULT, 'Fault'),
        ]
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='status_changes'
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for the status change"
    )
    
    class Meta:
        ordering = ['-changed_at']