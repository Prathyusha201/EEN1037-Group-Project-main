from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from machines.models import Machine


def create_warning(machine, text, severity='MEDIUM', user=None):
    """
    Create a new warning for a machine.
    If a similar active warning already exists, return it instead.
    """
    from warnings.models import Warning
    
    # Check if a similar active warning exists
    existing_warning = Warning.objects.filter(
        machine=machine,
        text=text,
        active=True
    ).first()
    
    if existing_warning:
        return existing_warning
    
    # Create new warning
    warning = Warning.objects.create(
        machine=machine,
        text=text,
        severity=severity,
        created_by=user
    )
    
    # Update machine status
    update_machine_status_from_warnings(machine)
    
    return warning


def resolve_warning(warning_id, user=None, note='', auto=False):
    """
    Resolve a warning by ID.
    """
    from warnings.models import Warning
    
    try:
        warning = Warning.objects.get(id=warning_id, active=True)
        warning.resolve(user=user, note=note, auto=auto)
        return True, warning
    except Warning.DoesNotExist:
        return False, None


def resolve_warnings_by_text(machine, text, user=None, note='', auto=False):
    """
    Resolve all active warnings on a machine matching the given text.
    """
    from warnings.models import Warning
    
    warnings = Warning.objects.filter(
        machine=machine,
        text=text,
        active=True
    )
    
    resolved_count = 0
    for warning in warnings:
        warning.resolve(user=user, note=note, auto=auto)
        resolved_count += 1
    
    return resolved_count


def resolve_all_warnings(machine, user=None, note='', auto=False):
    """
    Resolve all active warnings on a machine.
    """
    from warnings.models import Warning
    
    warnings = Warning.objects.filter(
        machine=machine,
        active=True
    )
    
    resolved_count = 0
    for warning in warnings:
        warning.resolve(user=user, note=note, auto=auto)
        resolved_count += 1
    
    return resolved_count


def get_active_warnings(machine=None):
    """
    Get all active warnings for a specific machine or all machines.
    """
    from warnings.models import Warning
    
    query = Q(active=True)
    if machine:
        query &= Q(machine=machine)
    
    return Warning.objects.filter(query)


def get_warnings_by_severity(severity, machine=None, active_only=True):
    """
    Get warnings filtered by severity level.
    """
    from warnings.models import Warning
    
    query = Q(severity=severity)
    if active_only:
        query &= Q(active=True)
    if machine:
        query &= Q(machine=machine)
    
    return Warning.objects.filter(query)


def update_machine_status_from_warnings(machine):
    """
    Update machine status based on its active warnings.
    If any active warnings exist, set status to WARNING.
    If no active warnings exist, check if the machine has active faults.
    If no active faults, set status to OK.
    """
    from warnings.models import Warning
    
    active_warnings_count = Warning.objects.filter(
        machine=machine,
        active=True
    ).count()
    
    # If machine has active faults, don't change the status
    if machine.status == 'FAULT' and machine.active_fault_cases().exists():
        return
    
    # Update status based on warnings
    if active_warnings_count > 0:
        if machine.status != 'WARNING':
            machine.set_status('WARNING', auto=True)
    else:
        # If no warnings and no faults, set to OK
        if machine.status != 'OK' and not machine.active_fault_cases().exists():
            machine.set_status('OK', auto=True)