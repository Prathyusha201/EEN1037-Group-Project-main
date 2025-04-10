from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from users.models import User


class Notification(models.Model):
    """
    Model to store notifications for users.
    Each notification can be linked to any object using
    the generic foreign key.
    """
    NOTIFICATION_TYPES = (
        ('WARNING_CREATED', _('Warning Created')),
        ('WARNING_RESOLVED', _('Warning Resolved')),
        ('FAULT_CREATED', _('Fault Created')),
        ('FAULT_UPDATED', _('Fault Updated')),
        ('FAULT_RESOLVED', _('Fault Resolved')),
        ('ASSIGNMENT_CHANGED', _('Assignment Changed')),
        ('COMMENT_ADDED', _('Comment Added')),
        ('MACHINE_STATUS_CHANGED', _('Machine Status Changed')),
    )
    
    SEVERITY_CHOICES = (
        ('LOW', _('Low')),
        ('MEDIUM', _('Medium')),
        ('HIGH', _('High')),
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    
    message = models.TextField(
        verbose_name=_('Message')
    )
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Recipient')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    read = models.BooleanField(
        default=False,
        verbose_name=_('Read')
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read At')
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        verbose_name=_('Notification Type')
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='MEDIUM',
        verbose_name=_('Severity')
    )
    
    # Generic foreign key to link notification to any object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    email_sent = models.BooleanField(
        default=False,
        verbose_name=_('Email Sent')
    )
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
    
    def mark_as_read(self):
        """
        Mark notification as read.
        """
        from django.utils import timezone
        self.read = True
        self.read_at = timezone.now()
        self.save()
        return self


class NotificationPreference(models.Model):
    """
    Model to store notification preferences for users.
    Users can specify which notification types they want to
    receive in-app and via email.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('User')
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=Notification.NOTIFICATION_TYPES,
        verbose_name=_('Notification Type')
    )
    
    in_app = models.BooleanField(
        default=True,
        verbose_name=_('In-App Notification')
    )
    
    email = models.BooleanField(
        default=True,
        verbose_name=_('Email Notification')
    )
    
    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
        unique_together = ('user', 'notification_type')
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"