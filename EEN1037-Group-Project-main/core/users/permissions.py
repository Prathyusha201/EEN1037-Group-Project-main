from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from functools import wraps
from django.shortcuts import redirect


def is_manager(user):
    """Check if user is a manager."""
    return user.is_authenticated and user.is_manager()


def is_technician(user):
    """Check if user is a technician."""
    return user.is_authenticated and user.is_technician()


def is_repair_staff(user):
    """Check if user is repair staff."""
    return user.is_authenticated and user.is_repair()


def has_higher_permission_than_view_only(user):
    """Check if user has permission higher than view-only."""
    return user.is_authenticated and not user.is_view_only()


def manager_required(function=None):
    """Decorator to restrict access to managers."""
    actual_decorator = user_passes_test(is_manager)
    if function:
        return actual_decorator(function)
    return actual_decorator


def technician_required(function=None):
    """Decorator to restrict access to technicians and higher roles."""
    def check_role(user):
        return user.is_authenticated and (user.is_technician() or user.is_repair() or user.is_manager())
    
    actual_decorator = user_passes_test(check_role)
    if function:
        return actual_decorator(function)
    return actual_decorator


def repair_required(function=None):
    """Decorator to restrict access to repair staff and higher roles."""
    def check_role(user):
        return user.is_authenticated and (user.is_repair() or user.is_manager())
    
    actual_decorator = user_passes_test(check_role)
    if function:
        return actual_decorator(function)
    return actual_decorator


def can_edit_machine(function):
    """Decorator to check if user can edit machine."""
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_manager():
            return function(request, *args, **kwargs)
        
        machine_id = kwargs.get('machine_id') or kwargs.get('pk')
        if not machine_id:
            return redirect('machines:list')
        
        # Check if user is assigned to the machine
        from users.models import UserMachineAssignment
        is_assigned = UserMachineAssignment.objects.filter(
            user=request.user,
            machine_id=machine_id
        ).exists()
        
        if is_assigned:
            return function(request, *args, **kwargs)
        
        raise PermissionDenied("You do not have permission to edit this machine.")
    
    return wrapper


def can_edit_case(function):
    """Decorator to check if user can edit a case."""
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        # Managers can edit all cases
        if request.user.is_manager():
            return function(request, *args, **kwargs)
        
        case_id = kwargs.get('case_id') or kwargs.get('pk')
        if not case_id:
            return redirect('cases:list')
        
        # Import here to avoid circular import
        from cases.models import Case
        from users.models import UserMachineAssignment
        
        try:
            case = Case.objects.get(pk=case_id)
            
            # Check if repair staff or technician is assigned to the machine
            is_assigned = UserMachineAssignment.objects.filter(
                user=request.user,
                machine=case.machine
            ).exists()
            
            # Repair staff can edit any case they're assigned to
            if request.user.is_repair() and is_assigned:
                return function(request, *args, **kwargs)
            
            # Technicians can edit cases they created or are assigned to
            if request.user.is_technician() and (is_assigned or case.created_by == request.user):
                return function(request, *args, **kwargs)
            
            raise PermissionDenied("You do not have permission to edit this case.")
            
        except Case.DoesNotExist:
            return redirect('cases:list')
    
    return wrapper


# Class-based view mixins
class ManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to managers."""
    def test_func(self):
        return is_manager(self.request.user)


class TechnicianRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to technicians and higher roles."""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_technician() or user.is_repair() or user.is_manager())


class RepairRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to repair staff and higher roles."""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_repair() or user.is_manager())


class EditMachinePermissionMixin(UserPassesTestMixin):
    """Mixin to check if user can edit a machine."""
    def test_func(self):
        # Managers can edit all machines
        if self.request.user.is_manager():
            return True
        
        # Get machine ID from URL kwargs
        machine_id = self.kwargs.get('machine_id') or self.kwargs.get('pk')
        if not machine_id:
            return False
        
        # Check if user is assigned to the machine
        from users.models import UserMachineAssignment
        return UserMachineAssignment.objects.filter(
            user=self.request.user,
            machine_id=machine_id
        ).exists()


class EditCasePermissionMixin(UserPassesTestMixin):
    """Mixin to check if user can edit a case."""
    def test_func(self):
        # Managers can edit all cases
        if self.request.user.is_manager():
            return True
        
        # Get case ID from URL kwargs
        case_id = self.kwargs.get('case_id') or self.kwargs.get('pk')
        if not case_id:
            return False
        
        # Import here to avoid circular import
        from cases.models import Case
        from users.models import UserMachineAssignment
        
        try:
            case = Case.objects.get(pk=case_id)
            
            # Check if user is assigned to the machine
            is_assigned = UserMachineAssignment.objects.filter(
                user=self.request.user,
                machine=case.machine
            ).exists()
            
            # Repair staff can edit any case they're assigned to
            if self.request.user.is_repair() and is_assigned:
                return True
            
            # Technicians can edit cases they created or are assigned to
            if self.request.user.is_technician() and (is_assigned or case.created_by == self.request.user):
                return True
            
            return False
            
        except Case.DoesNotExist:
            return False