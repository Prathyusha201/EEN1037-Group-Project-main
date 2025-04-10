"""
Utility functions for case management.
"""
from django.db.models import Count, Q, Case as DjangoCase, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from cases.models import Case, CaseStatus, CasePriority

def get_prioritized_cases(user=None, limit=None):
    """
    Get cases sorted by priority score.
    
    Args:
        user: Optional user to filter cases by assignment
        limit: Optional limit on number of cases returned
        
    Returns:
        QuerySet: Prioritized cases
    """
    from cases.workflow import CaseWorkflow
    
    # Start with all unresolved cases
    queryset = Case.objects.filter(
        status__in=[CaseStatus.OPEN, CaseStatus.IN_PROGRESS]
    )
    
    # Filter by user if specified
    if user and not user.is_staff:  # Staff can see all cases
        user_machines = user.assigned_machines.all()
        queryset = queryset.filter(
            Q(assigned_to=user) | Q(machine__in=user_machines)
        )
    
    # Annotate with age in days
    queryset = queryset.annotate(
        age_days=DjangoCase(
            When(created_at__lt=timezone.now() - timedelta(days=30), then=30),
            default=(timezone.now() - models.F('created_at')) / timedelta(days=1),
            output_field=IntegerField()
        )
    )
    
    # Order by priority, status, and age
    queryset = queryset.annotate(
        priority_value=DjangoCase(
            When(priority=CasePriority.CRITICAL, then=4),
            When(priority=CasePriority.HIGH, then=3),
            When(priority=CasePriority.MEDIUM, then=2),
            When(priority=CasePriority.LOW, then=1),
            default=0,
            output_field=IntegerField()
        ),
        status_value=DjangoCase(
            When(status=CaseStatus.OPEN, then=2),
            When(status=CaseStatus.IN_PROGRESS, then=1),
            default=0,
            output_field=IntegerField()
        )
    ).order_by('-priority_value', '-status_value', '-age_days')
    
    # Apply limit if specified
    if limit:
        queryset = queryset[:limit]
        
    return queryset

def generate_case_statistics(start_date=None, end_date=None, machines=None):
    """
    Generate statistics about cases for reporting.
    
    Args:
        start_date: Optional start date for the report period
        end_date: Optional end date for the report period
        machines: Optional list of machines to filter by
        
    Returns:
        dict: Statistics about cases
    """
    # Base queryset
    queryset = Case.objects.all()
    
    # Apply date filters
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    # Apply machine filter
    if machines:
        queryset = queryset.filter(machine__in=machines)
    
    # Calculate statistics
    total_cases = queryset.count()
    open_cases = queryset.filter(status=CaseStatus.OPEN).count()
    in_progress_cases = queryset.filter(status=CaseStatus.IN_PROGRESS).count()
    resolved_cases = queryset.filter(status=CaseStatus.RESOLVED).count()
    closed_cases = queryset.filter(status=CaseStatus.CLOSED).count()
    
    # Calculate average resolution time
    avg_resolution_time = None
    resolved_cases_with_time = queryset.filter(
        status__in=[CaseStatus.RESOLVED, CaseStatus.CLOSED],
        resolved_at__isnull=False
    )
    
    if resolved_cases_with_time.exists():
        from django.db.models import Avg, F, ExpressionWrapper, fields
        avg_resolution_time = resolved_cases_with_time.annotate(
            resolution_time=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=fields.DurationField()
            )
        ).aggregate(avg_time=Avg('resolution_time'))['avg_time']
    
    # Cases by priority
    cases_by_priority = queryset.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    # Cases by machine
    cases_by_machine = queryset.values(
        'machine__id', 'machine__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 machines
    
    return {
        'total_cases': total_cases,
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'resolved_cases': resolved_cases,
        'closed_cases': closed_cases,
        'avg_resolution_time': avg_resolution_time,
        'cases_by_priority': list(cases_by_priority),
        'cases_by_machine': list(cases_by_machine),
    }

def export_case_report(cases, format='csv'):
    """
    Export cases to a formatted report.
    
    Args:
        cases: QuerySet of cases to export
        format: Format to export (csv, excel, pdf)
        
    Returns:
        bytes: File data in the requested format
    """
    import csv
    import io
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Case Number', 'Title', 'Machine', 'Status', 'Priority',
            'Created By', 'Assigned To', 'Created At', 'Updated At',
            'Resolved At', 'Description'
        ])
        
        # Write data
        for case in cases:
            writer.writerow([
                case.case_number,
                case.title,
                case.machine.name,
                case.get_status_display(),
                case.get_priority_display(),
                case.created_by.username if case.created_by else 'N/A',
                case.assigned_to.username if case.assigned_to else 'Unassigned',
                case.created_at.strftime('%Y-%m-%d %H:%M'),
                case.updated_at.strftime('%Y-%m-%d %H:%M'),
                case.resolved_at.strftime('%Y-%m-%d %H:%M') if case.resolved_at else 'N/A',
                case.description
            ])
        
        return output.getvalue().encode('utf-8')
    
    elif format == 'excel':
        # Implementation for Excel export would go here
        # Using a library like openpyxl or xlsxwriter
        pass
    
    elif format == 'pdf':
        # Implementation for PDF export would go here
        # Using a library like ReportLab
        pass
    
    else:
        raise ValueError(f"Unsupported export format: {format}")