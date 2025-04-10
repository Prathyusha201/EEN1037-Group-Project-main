from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_notification_email_to_user(notification):
    """
    Send email for a notification to the recipient.
    
    Args:
        notification: Notification object
    
    Returns:
        bool: Success status
    """
    if not notification or notification.email_sent:
        return False
    
    recipient = notification.recipient
    if not recipient.email:
        return False
    
    # Prepare context for email template
    context = {
        'user': recipient,
        'notification': notification,
        'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'ACME Manufacturing',
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else '/',
    }
    
    # If there's a related object, add its details
    if notification.related_object:
        context['related_object'] = notification.related_object
        
        # Add URL for the related object if applicable
        if hasattr(notification.related_object, 'get_absolute_url'):
            context['object_url'] = notification.related_object.get_absolute_url()
    
    # Render HTML content
    html_content = render_to_string('notifications/email_notification.html', context)
    
    # Create plain text version
    text_content = strip_tags(html_content)
    
    # Send email
    try:
        send_mail(
            subject=notification.title,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_content,
            fail_silently=False
        )
        
        # Mark notification as emailed
        notification.email_sent = True
        notification.save(update_fields=['email_sent'])
        
        return True
    except Exception as e:
        # Log the error but don't raise it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send notification email to {recipient.email}: {str(e)}")
        
        return False