from celery import shared_task
from django.utils import timezone
from apps.workflow.models import Output
from apps.assignments.models import Assignment

@shared_task(name="config.celery.check_workflow_deadlines")
def check_workflow_deadlines():
    """
    Фоновая периодическая задача контроля сроков выходов НИР.
    Соответствует требованиям Документа №15 (раздел 22, 30).
    """
    now = timezone.now().date()
    
    # 1. Поиск выходов, у которых наступил или прошел дедлайн, но они не завершены
    # Вычисляемый признак просрочки (раздел 12 Документа №14)
    overdue_outputs = Output.objects.filter(
        deadline__lte=now,
        status__in=['new', 'in_progress', 'returned']
    ).select_related('task__stage__project__manager')
    
    for output in overdue_outputs:
        # Получаем всех исполнителей данного выхода
        assignments = Assignment.objects.filter(output=output).select_related('employee__user')
        
        # Формируем рассылку для каждого участника (Исполнитель, Ответственный, Руководитель)
        # в соответствии с разделом 13 Документа №15
        recipients = []
        for asn in assignments:
            recipients.append({
                "email": asn.employee.user.email,
                "role": "responsible" if asn.is_responsible else "executor"
            })
            
        # Добавляем руководителя проекта в получатели
        if output.task.stage.project.manager:
            recipients.append({
                "email": output.task.stage.project.manager.user.email,
                "role": "manager"
            })
            
        # Здесь будет логика генерации уведомлений через event_bus (раздел 20 Сервисного слоя)
        # Для демонстрации в логах Celery:
        print(f"[CRITICAL DEADLINE] Выход '{output.name}' ПРОСРОЧЕН! Срок: {output.deadline}. "
              f"Уведомления подготовлены для {len(recipients)} получателей.")
              
    return f"Проверка завершена. Найдено просроченных выходов: {overdue_outputs.count()}"