from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

# ПРАВИЛЬНЫЕ ПУТИ ИМПОРТА
from apps.organization.models import Department, DepartmentMembership
from apps.reporting.selectors import get_department_load
from apps.projects.models import Project
from apps.workflow.models import Stage
from apps.assignments.models import Assignment


def department_load_page(request):
    departments = Department.objects.filter(is_active=True).order_by('name')
    return render(request, 'reporting/department_load.html', {'departments': departments})


def department_load_fragment(request):
    department_id = request.GET.get('department_id')
    if not department_id:
        return render(request, 'reporting/partials/load_table_fragment.html', {'data': None})
    
    load_data = get_department_load(department_id=department_id)
    return render(request, 'reporting/partials/load_table_fragment.html', {'data': load_data})


def is_management(user):
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=['Managers', 'Directors']).exists() or getattr(user, 'role', '') in ['manager', 'director']


@login_required
def management_dashboard_view(request):
    if not is_management(request.user):
        raise PermissionDenied("Доступ разрешен только руководству института.")

    now = timezone.now().date()

    total_projects = Project.objects.exclude(status='completed').count()
    total_employees = DepartmentMembership.objects.filter(is_primary=True).values('employee_id').distinct().count()

    overdue_projects_count = Project.objects.filter(
        end_date__lt=now
    ).exclude(status='completed').count()

    overdue_stages_count = Stage.objects.filter(
        end_date__lt=now
    ).exclude(status='completed').count()

    departments = Department.objects.all().order_by('name')

    context = {
        'total_projects': total_projects,
        'total_employees': total_employees,
        'system_overdue_count': overdue_projects_count + overdue_stages_count,
        'departments': departments,
    }
    return render(request, 'reporting/management_dashboard.html', context)


@login_required
def financial_overview_widget(request):
    if not is_management(request.user):
        raise PermissionDenied

    total_projects_count = Project.objects.count()

    type_counts = Project.objects.values('project_type').annotate(
        count=Count('id')
    ).order_by('-count')

    finance_breakdown = []
    for item in type_counts:
        cnt = item['count']
        percentage = round((cnt / total_projects_count) * 100) if total_projects_count > 0 else 0
        finance_breakdown.append({
            'contract_type': item['project_type'] or 'Без типа',
            'count': cnt,
            'percentage': percentage,
        })

    return render(request, 'reporting/partials/financial_overview.html', {
        'finance_breakdown': finance_breakdown,
        'total_projects_count': total_projects_count,
    })


@login_required
def critical_alerts_widget(request):
    if not is_management(request.user):
        raise PermissionDenied

    now = timezone.now().date()
    stale_threshold = timezone.now() - timedelta(days=7)

    overdue_projects = Project.objects.filter(
        end_date__lt=now
    ).exclude(status='completed').select_related('manager')[:5]

    overdue_stages = Stage.objects.filter(
        end_date__lt=now
    ).exclude(status='completed').select_related('project')[:5]

    stagnant_assignments = Assignment.objects.filter(
        assigned_at__lte=stale_threshold
    ).select_related('output', 'employee__user').order_by('assigned_at')[:5]

    return render(request, 'reporting/partials/critical_alerts.html', {
        'overdue_projects': overdue_projects,
        'overdue_stages': overdue_stages,
        'stagnant_assignments': stagnant_assignments,
    })