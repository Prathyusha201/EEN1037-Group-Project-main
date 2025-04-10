"""
Implements the case workflow state machine and business rules
for transitioning between different case states.
"""
from cases.models import CaseStatus
from machines.models import MachineStatus
from django.utils import timezone

class CaseWorkflow:
    """
    Class handling the case state machine implementation and 
    business rules for case transitions.
    """
    
    # Valid transitions from each status
    VALID_TRANSITIONS = {
        CaseStatus.OPEN: [CaseStatus.IN_PROGRESS, CaseStatus.CLOSED],
        CaseStatus.IN_PROGRESS: [CaseStatus.RESOLVED, CaseStatus.OPEN],
        CaseStatus.RESOLVED: [CaseStatus.CLOSED, CaseStatus.IN_PROGRESS],
        CaseStatus.CLOSED: []  # No transitions from CLOSED
    }
    
    # Role permissions for each transition
    TRANSITION_PERMISSIONS = {
        # Who can transition from OPEN to other states
        (CaseStatus.OPEN, CaseStatus.IN_PROGRESS): ['repair', 'manager'],
        (CaseStatus.OPEN, CaseStatus.CLOSED): ['manager'],
        
        # Who can transition from IN_PROGRESS to other states
        (CaseStatus.IN_PROGRESS, CaseStatus.RESOLVED): ['repair', 'manager'],
        (CaseStatus.IN_PROGRESS, CaseStatus.OPEN): ['repair', 'manager'],
        
        # Who can transition from RESOLVED to other states
        (CaseStatus.RESOLVED, CaseStatus.CLOSED): ['technician', 'manager'],
        (CaseStatus.RESOLVED, CaseStatus.IN_PROGRESS): ['repair', 'manager'],
    }
    
    @classmethod
    def can_transition(cls, current_status, new_status):
        """
        Check if the status transition is valid according to the workflow.
        
        Args:
            current_status (str): Current case status
            new_status (str): Target case status
            
        Returns:
            bool: True if transition is allowed, False otherwise
        """
        return new_status in cls.VALID_TRANSITIONS.get(current_status, [])
    
    @classmethod
    def can_user_transition(cls, user, current_status, new_status):
        """
        Check if the user has permission to perform this transition.
        
        Args:
            user: The user attempting the transition
            current_status (str): Current case status
            new_status (str): Target case status
            
        Returns:
            bool: True if user can perform this transition, False otherwise
        """
        if not cls.can_transition(current_status, new_status):
            return False
            
        allowed_roles = cls.TRANSITION_PERMISSIONS.get((current_status, new_status), [])
        user_roles = [group.name.lower() for group in user.groups.all()]
        
        # Managers can do all transitions
        if 'manager' in user_roles:
            return True
            
        # Check if user has any of the allowed roles
        return any(role in allowed_roles for role in user_roles)
    
    @classmethod
    def calculate_machine_status_after_resolution(cls, machine):
        """
        Calculate machine status after a case is resolved.
        
        Args:
            machine: The machine object to evaluate
            
        Returns:
            str: The new machine status
        """
        # Check if there are any unresolved cases
        open_cases = machine.cases.filter(
            status__in=[CaseStatus.OPEN, CaseStatus.IN_PROGRESS]
        ).exists()
        
        if open_cases:
            return MachineStatus.FAULT
            
        # Check if there are active warnings
        has_warnings = machine.warnings.filter(active=True).exists()
        
        if has_warnings:
            return MachineStatus.WARNING
            
        # No warnings or open cases - machine is OK
        return MachineStatus.OK
    
    @classmethod
    def get_case_priority_score(cls, case):
        """
        Calculate a numerical priority score for a case based on
        priority level, age, and machine importance.
        
        Args:
            case: The case to evaluate
            
        Returns:
            int: Priority score (higher = more important)
        """
        # Base priority scores
        priority_scores = {
            'CRITICAL': 1000,
            'HIGH': 500,
            'MEDIUM': 100,
            'LOW': 10
        }
        
        # Get base score
        base_score = priority_scores.get(case.priority, 0)
        
        # Add age factor (older cases get higher priority)
        age_in_days = (timezone.now() - case.created_at).days
        age_score = min(age_in_days * 5, 100)  # Cap at 100 (20 days)
        
        # Add machine importance factor
        machine_importance = case.machine.importance or 1
        
        # Calculate final score
        return base_score + age_score + (machine_importance * 50)