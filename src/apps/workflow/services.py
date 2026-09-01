from django.core.exceptions import ValidationError
from django.db import transaction
from apps.workflow.models import Output
from apps.organization.models import Employee
from apps.audit.services import log_action  # Импортируем наш сервис аудита

def start_output(*, actor: Employee, output: Output) -> Output:
    """Перевод Выхода из статуса 'Новый' в 'В работе' с записью аудита."""
    if output.status != 'new':
        raise ValidationError(f"Нельзя начать работу по выходу со статусом {output.get_status_display()}.")
    
    # Фиксируем старое состояние для журнала изменений
    old_status = output.get_status_display()
    
    with transaction.atomic():
        output.status = 'in_progress'
        output.save()
        
        # Регистрируем событие сквозного аудита
        log_action(
            user=actor.user,
            action="OUTPUT_STATUS_CHANGED",
            entity=output,
            old_value={"status": "new", "status_display": old_status},
            new_value={"status": "in_progress", "status_display": output.get_status_display()}
        )
        
    return output


def complete_output(*, actor: Employee, output: Output) -> Output:
    """
    Утверждение Выхода руководителем проекта (Завершение работы) с записью аудита.
    """
    if output.status != 'submitted':
        raise ValidationError("Завершить можно только тот выход, который находится на проверке.")
    
    # Проверка контекстных прав (Документ №12, Раздел 5)
    project = output.task.stage.project
    if project.manager != actor:
        raise ValidationError("Только руководитель проекта может принять выполнение выхода.")

    old_status = output.get_status_display()

    with transaction.atomic():
        output.status = 'completed'
        output.save()
        
        # Синхронно-асинхронный аудит критического действия
        log_action(
            user=actor.user,
            action="OUTPUT_COMPLETED",
            entity=output,
            old_value={"status": "submitted", "status_display": old_status},
            new_value={"status": "completed", "status_display": output.get_status_display()}
        )
        
    return output


def return_output(*, actor: Employee, output: Output, comment: str) -> Output:
    """Возврат Выхода руководителем на доработку с фиксацией причины в аудите."""
    if output.status != 'submitted':
        raise ValidationError("Вернуть на доработку можно только выход, находящийся на проверке.")
        
    project = output.task.stage.project
    if project.manager != actor:
        raise ValidationError("Только руководитель проекта может вернуть выход на доработку.")
        
    if not comment.strip():
        raise ValidationError("При возврате на доработку обязательно нужно указать причину/комментарий.")

    old_status = output.get_status_display()

    with transaction.atomic():
        output.status = 'returned'
        output.save()
        
        # Логируем изменение статуса и прикрепляем комментарий руководителя в метаданные
        log_action(
            user=actor.user,
            action="OUTPUT_RETURNED",
            entity=output,
            old_value={"status": "submitted", "status_display": old_status},
            new_value={
                "status": "returned", 
                "status_display": output.get_status_display(),
                "comment": comment
            }
        )
        
    return output