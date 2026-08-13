from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from src.apps.workflow.models import Output
from src.apps.organization.models import Employee

def start_output(*, actor: Employee, output: Output) -> Output:
    """Перевод Выхода из статуса 'Новый' в 'В работе'."""
    if output.status != 'new':
        raise ValidationError(f"Нельзя начать работу по выходу со статусом {output.get_status_display()}.")
    
    output.status = 'in_progress'
    output.save()
    
    # ТУТ БУДЕТ ВЫЗОВ: event_bus.publish(OutputStarted(...))
    return output


def submit_output(*, actor: Employee, output: Output) -> Output:
    """Передача Выхода исполнителем на проверку руководителю."""
    if output.status not in ['in_progress', 'returned']:
        raise ValidationError("На проверку можно отправить только выходы 'В работе' или 'На доработке'.")
        
    output.status = 'submitted'
    output.save()
    
    # ТУТ БУДЕТ ВЫЗОВ: event_bus.publish(OutputSubmitted(...))
    return output


def complete_output(*, actor: Employee, output: Output) -> Output:
    """
    Утверждение Выхода руководителем (Завершение работы).
    """
    if output.status != 'submitted':
        raise ValidationError("Завершить можно только тот выход, который находится на проверке.")
    
    # Проверка прав: actor должен быть руководителем проекта
    project = output.task.stage.project
    if project.manager != actor:
        raise ValidationError("Только руководитель проекта может принять выполнение выхода.")

    with transaction.atomic():
        output.status = 'completed'
        output.save()
        
        # Фиксация даты завершения и создание записи сквозного аудита
        # ТУТ БУДЕТ ВЫЗОВ: audit.log(actor=actor, action="OUTPUT_COMPLETED", entity=output)
        # ТУТ БУДЕТ ВЫЗОВ: event_bus.publish(OutputCompleted(...)) -> отправка через Celery
        
    return output


def return_output(*, actor: Employee, output: Output, comment: str) -> Output:
    """Возврат Выхода руководителем на доработку исполнителям."""
    if output.status != 'submitted':
        raise ValidationError("Вернуть на доработку можно только выход, находящийся на проверке.")
        
    project = output.task.stage.project
    if project.manager != actor:
        raise ValidationError("Только руководитель проекта может вернуть выход на доработку.")
        
    if not comment.strip():
        raise ValidationError("При возврате на доработку обязательно нужно указать причину/комментарий.")

    with transaction.atomic():
        output.status = 'returned'
        output.save()
        
        # Комментарий сохраняется в историю изменений (Audit/Comments)
        # ТУТ БУДЕТ ВЫЗОВ: event_bus.publish(OutputReturned(...))
        
    return output