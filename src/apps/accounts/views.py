from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.organization.models import DepartmentMembership
# Предполагается наличие моделей Order и Assignment в соответствующих приложениях

@login_required
def profile_page(request):
    memberships = DepartmentMembership.objects.filter(employee__user=request.user)
    # Заглушки для QuerySet'ов поручений и выходов
    tasks = [] # Order.objects.filter(assignee=request.user.employee_profile, status__in=['new', 'in_progress', 'returned'])
    outputs = [] # Assignment.objects.filter(assignee=request.user.employee_profile).order_by('deadline')
    
    return render(request, 'accounts/profile.html', {
        'memberships': memberships,
        'tasks': tasks,
        'outputs': outputs
    })