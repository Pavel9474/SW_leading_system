from django.contrib.contenttypes.models import ContentType
from apps.audit.models import AuditLog
from apps.audit.tasks import async_write_audit_metadata

def log_action(
    *,
    user,
    action: str,
    entity,
    old_value: dict = None,
    new_value: dict = None,
    ip_address: str = None
) -> AuditLog:
    """
    Основной интерфейс сквозного логирования действий в системе.
    Синхронно создает каркас лога, а тяжелые JSON данные отдает в Celery.
    """
    entity_content_type = ContentType.objects.get_for_model(entity)
    
    # 1. Синхронная быстрая вставка каркаса в рамках текущей транзакции
    log_entry = AuditLog.objects.create(
        user=user,
        action=action,
        content_type=entity_content_type,
        object_id=entity.id,
        ip_address=ip_address
    )
    
    # 2. Передача тяжелых JSON-данных на асинхронную обработку воркеру Celery
    if old_value or new_value:
        async_write_audit_metadata.delay(
            log_id=str(log_entry.id),
            old_value=old_value,
            new_value=new_value
        )
        
    return log_entry