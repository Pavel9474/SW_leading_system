from django.db.models import Count, Q
from src.apps.organization.models import Department
from src.apps.assignments.models import Assignment
from src.apps.workflow.models import Output

def get_department_load(*, department_id: str) -> dict:
    """
    Архитектурный селектор агрегации нагрузки на подразделение.
    Исключает двойной учет сотрудников за счет фильтрации по department_membership.
    """
    # Проверяем существование подразделения
    try:
        department = Department.objects.get(id=department_id)
    except Department.DoesNotExist:
        return {"error": "Подразделение не найдено"}

    # 1. Считаем количество уникальных сотрудников, закрепленных за отделом/лабораторией
    # (учитываем как основных, так и совместителей)
    total_employees = department.memberships.filter(employee__is_active=True).values('employee_id').distinct().count()

    # 2. Агрегируем Выходы (Outputs), назначенные на сотрудников данного подразделения
    # Фильтрация идет строго через department_membership этого подразделения!
    outputs_count = Assignment.objects.filter(
        department_membership__department_id=department_id,
        output__status__in=['in_progress', 'submitted', 'returned'] # Только активные в работе
    ).values('output_id').distinct().count()

    # 3. Детализация по каждому сотруднику подразделения для интерфейса руководителя
    employees_metrics = []
    memberships = department.memberships.filter(employee__is_active=True).select_related('employee', 'position')
    
    for mem in memberships:
        # Считаем выходы конкретного сотрудника строго в рамках текущей кадровой роли
        emp_outputs = Assignment.objects.filter(
            department_membership=mem,
            output__status__in=['in_progress', 'submitted', 'returned']
        ).count()
        
        # Считаем, за сколько выходов он отвечает как Ответственный исполнитель
        responsible_count = Assignment.objects.filter(
            department_membership=mem,
            is_responsible=True,
            output__status__in=['in_progress', 'submitted', 'returned']
        ).count()

        employees_metrics.append({
            "employee_id": str(mem.employee.id),
            "full_name": f"{mem.employee.last_name} {mem.employee.first_name}",
            "position": mem.position.name,
            "is_primary": mem.is_primary,
            "active_outputs": emp_outputs,
            "responsible_outputs": responsible_count
        })

    return {
        "department_id": str(department.id),
        "department_name": department.name,
        "total_employees": total_employees,
        "aggregated_active_outputs": outputs_count,
        "employees_detail": employees_metrics
    }