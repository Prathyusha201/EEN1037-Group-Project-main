"""
Custom model managers for Machine models.
"""
from django.db import models


class MachineQuerySet(models.QuerySet):
    """Custom QuerySet for Machine model with additional filtering methods."""
    
    def by_status(self, status):
        """
        Filters machines by their current status.
        This is a complex query as status is a computed property.
        
        Args:
            status: The status to filter by (OK, Warning, or Fault)
            
        Returns:
            QuerySet: Filtered queryset of machines
        """
        from machines.models import Machine
        from cases.models import Case
        from warnings.models import Warning
        
        if status == Machine.STATUS_FAULT:
            # Machines with open fault cases
            machine_ids = Case.objects.filter(
                status__in=['open', 'in_progress']
            ).values_list('machine_id', flat=True)
            return self.filter(id__in=machine_ids)
            
        elif status == Machine.STATUS_WARNING:
            # Machines with active warnings but no open fault cases
            fault_machine_ids = Case.objects.filter(
                status__in=['open', 'in_progress']
            ).values_list('machine_id', flat=True)
            
            warning_machine_ids = Warning.objects.filter(
                is_active=True
            ).values_list('machine_id', flat=True)
            
            return self.filter(
                id__in=warning_machine_ids
            ).exclude(
                id__in=fault_machine_ids
            )
            
        elif status == Machine.STATUS_OK:
            # Machines with no active warnings and no open fault cases
            fault_machine_ids = Case.objects.filter(
                status__in=['open', 'in_progress']
            ).values_list('machine_id', flat=True)
            
            warning_machine_ids = Warning.objects.filter(
                is_active=True
            ).values_list('machine_id', flat=True)
            
            return self.exclude(
                id__in=fault_machine_ids
            ).exclude(
                id__in=warning_machine_ids
            )
            
        return self.none()
    
    def by_collection(self, collection):
        """
        Filters machines by collection membership.
        
        Args:
            collection: A MachineCollection instance or ID
            
        Returns:
            QuerySet: Filtered queryset of machines
        """
        return self.filter(collections=collection)
    
    def assigned_to(self, user):
        """
        Filters machines assigned to a specific user.
        
        Args:
            user: A User instance
            
        Returns:
            QuerySet: Filtered queryset of machines
        """
        if user.role == 'Technician':
            return self.filter(assigned_technicians=user)
        elif user.role == 'Repair':
            return self.filter(assigned_repair=user)
        elif user.role == 'Manager':
            # Managers can see all machines
            return self
        else:
            # View-only users don't have assigned machines
            return self.none()


class MachineManager(models.Manager):
    """Custom manager for Machine model."""
    
    def get_queryset(self):
        """Returns the custom queryset."""
        return MachineQuerySet(self.model, using=self._db)
    
    def by_status(self, status):
        """Filters machines by their current status."""
        return self.get_queryset().by_status(status)
    
    def by_collection(self, collection):
        """Filters machines by collection."""
        return self.get_queryset().by_collection(collection)
    
    def assigned_to(self, user):
        """Filters machines assigned to a user."""
        return self.get_queryset().assigned_to(user)