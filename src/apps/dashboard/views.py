from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.dashboard.selectors import get_dashboard_context

@login_required
def dashboard_index(request):
    context = get_dashboard_context(user=request.user)
    return render(request, 'dashboard/index.html', context)

@login_required
def lazy_department_load(request):
    """Ленивая подгрузка тяжелого виджета нагрузок"""
    # Здесь вызывается селектор get_department_load()
    return render(request, 'dashboard/partials/department_load.html')