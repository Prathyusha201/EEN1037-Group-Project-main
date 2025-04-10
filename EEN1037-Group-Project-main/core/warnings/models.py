from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from machines.models import Machine
from users.models import User


class Warning(models.Model):
    """
    Model to store machine warnings.
    A machine can have multiple active warnings.
    """
    SEVERITY_CHOICES = (
        ('LOW', _('Low')),
        ('MEDIUM', _('Medium')),
        ('HIGH', _('High')),
    )

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='warnings',
        verbose_name=_('Machine')
    )
    
    text = models.CharField(
        max_length=255,
        verbose_name=_('Warning Text')
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='MEDIUM',
        verbose_name=_('Severity')
    )
    
    active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_warnings',
        verbose_name=_('Created By')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_warnings',
        verbose_name=_('Resolved By')
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Resolved At')
    )
    
    resolution_note = models.TextField(
        blank=True,
        verbose_name=_('Resolution Note')
    )
    
    auto_resolution = models.BooleanField(
        default=False,
        verbose_name=_('Auto Resolution')
    )
    
    class Meta:
        verbose_name = _('Warning')
        verbose_name_plural = _('Warnings')
        unique_together = ('machine', 'text', 'active')  # Prevent duplicate active warnings
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.machine.name} - {self.text[:50]}"
    
    def resolve(self, user=None, note='', auto=False):
        """
        Resolve the warning.
        """
        self.active = False
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_note = note
        self.auto_resolution = auto
        self.save()
        
        # Update machine status if needed
        from warnings.utils import update_machine_status_from_warnings
        update_machine_status_from_warnings(self.machine)
        
        return self