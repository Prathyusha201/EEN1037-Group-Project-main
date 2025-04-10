from django.db import models
from django.utils import timezone
from django.conf import settings
from machines.models import Machine

class CaseStatus(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    RESOLVED = 'RESOLVED', 'Resolved'
    CLOSED = 'CLOSED', 'Closed'

class CasePriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical'

class Case(models.Model):
    """
    Represents a fault case for a machine that needs repair.
    Each case has a unique case number, status, and history of actions.
    """
    case_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='cases')
    status = models.CharField(
        max_length=20, 
        choices=CaseStatus.choices,
        default=CaseStatus.OPEN
    )
    priority = models.CharField(
        max_length=20,
        choices=CasePriority.choices,
        default=CasePriority.MEDIUM
    )
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cases'
    )
    
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cases')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.case_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generate case number if new case
        if not self.case_number:
            prefix = 'CASE'
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            self.case_number = f"{prefix}-{timestamp}-{self.machine.id}"
        
        # Handle status transitions
        if self.status == CaseStatus.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        if self.status == CaseStatus.CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def can_transition_to(self, new_status):
        """Check if the case status can transition to the new status"""
        from cases.workflow import CaseWorkflow
        return CaseWorkflow.can_transition(self.status, new_status)
    
    def transition_to(self, new_status, user=None):
        """Transition the case to a new status with validation"""
        from cases.workflow import CaseWorkflow
        
        if self.can_transition_to(new_status):
            old_status = self.status
            self.status = new_status
            self.save()
            
            # Create status change entry
            CaseStatusChange.objects.create(
                case=self,
                from_status=old_status,
                to_status=new_status,
                changed_by=user
            )
            
            # Update machine status if case is resolved
            if new_status == CaseStatus.RESOLVED:
                self.machine.check_status_after_case_resolution(self)
                
            return True
        return False

class CaseImage(models.Model):
    """
    Images attached to a case as evidence or documentation.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='case_images/%Y/%m/%d/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.case.case_number}"

class CaseComment(models.Model):
    """
    Comments and notes added to a case by technicians, managers, or repair personnel.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.case.case_number} by {self.created_by}"

class CaseStatusChange(models.Model):
    """
    Tracks history of status changes for a case.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='status_changes')
    from_status = models.CharField(max_length=20, choices=CaseStatus.choices)
    to_status = models.CharField(max_length=20, choices=CaseStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.case.case_number}: {self.from_status} → {self.to_status}"

class CaseAssignmentHistory(models.Model):
    """
    Tracks history of case assignments to different personnel.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='assignment_history')
    assigned_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_from'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_to'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-assigned_at']
    
    def __str__(self):
        from_user = self.assigned_from.username if self.assigned_from else 'None'
        to_user = self.assigned_to.username if self.assigned_to else 'None'
        return f"{self.case.case_number}: {from_user} → {to_user}"