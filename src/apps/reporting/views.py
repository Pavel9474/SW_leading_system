from django.shortcuts import render
from apps.organization.models import Department
from apps.reporting.selectors import get_department_load

def department_load_page(request):
    """
    Отображает главную страницу мониторинга нагрузки руководителя.
    Передает список всех активных подразделений для селектора выбора.
    """
    # Получаем список подразделений для выпадающего списка в интерфейсе
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'departments': departments
    }
    return render(request, 'reporting/department_load.html', context)


def department_load_fragment(request):
    """
    Эндпоинт для HTMX-запросов. Возвращает изолированный HTML-фрагмент 
    с результатами расчетов нагрузки для конкретного подразделения.
    """
    department_id = request.GET.get('department_id')
    
    # Если подразделение не выбрано, возвращаем заглушку
    if not department_id:
        return render(request, 'reporting/partials/load_table_fragment.html', {'data': None})
    
    # Извлекаем агрегированные очищенные данные через архитектурный селектор
    load_data = get_department_load(department_id=department_id)
    
    context = {
        'data': load_data
    }
    return render(request, 'reporting/partials/load_table_fragment.html', context)