from celery import shared_task
from src.apps.audit.models import AuditLog

@shared_task(name="config.celery.async_write_audit_metadata")
def async_write_audit_metadata(log_id: str, old_value: dict, new_value: dict):
    """
    Асинхронное обогащение лога аудита детальными метаданными.
    Снижает нагрузку на основную транзакцию БД.
    """
    try:
        log_entry = AuditLog.objects.get(id=log_id)
        log_entry.old_value = old_value
        log_entry.new_value = new_value
        log_entry.save(update_fields=['old_value', 'new_value'])
        return f"Метаданные лога {log_id} успешно сохранены."
    except AuditLog.DoesNotExist:
        return f"Ошибка: Лог аудита {log_id} не найден."