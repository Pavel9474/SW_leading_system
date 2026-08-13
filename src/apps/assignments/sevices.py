from django.core.exceptions import ValidationError
from django.db import transaction
from src.apps.assignments.models import Assignment
from src.apps.workflow.models import Output
from src.apps.organization.models import Employee, DepartmentMembership

def assign_executor(
    *,
    actor: Employee,
    output: Output,
    employee: Employee,
    department_membership: DepartmentMembership
) -> Assignment:
    """
    Бизнес-сервис назначения исполнителя на Выход с фиксацией подразделения.
    """
    # 1. Проверка прав инициатора (actor)
    project = output.task.stage.project
    if project.manager != actor:
        raise ValidationError("Только руководитель проекта может назначать исполнителей.")

    # 2. Проверка активности назначаемого сотрудника
    if not employee.is_active:
        raise ValidationError("Невозможно назначить неактивного сотрудника.")

    # 3. Валидация кадровой роли: принадлежит ли membership именно этому сотруднику
    if department_membership.employee != employee:
        raise ValidationError(
            f"Указанная кадровая роль не принадлежит сотруднику {employee}."
        )

    # 4. Проверка существующего назначения
    existing_assignment = Assignment.objects.filter(
        output=output, 
        employee=employee,
        department_membership=department_membership
    ).first()
    
    if existing_assignment:
        return existing_assignment

    with transaction.atomic():
        # Если это самый первый исполнитель на данном выходе, сделаем его ответственным
        is_first = not Assignment.objects.filter(output=output).exists()

        assignment = Assignment.objects.create(
            output=output,
            employee=employee,
            department_membership=department_membership,
            is_responsible=is_first
        )

        # ТУТ БУДЕТ ВЫЗОВ: audit.log(actor, "EXECUTOR_ASSIGNED", assignment)
        # ТУТ БУДЕТ ВЫЗОВ: event_bus.publish(ExecutorAssigned(assignment_id=assignment.id))

        return assignment