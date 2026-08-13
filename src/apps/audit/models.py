import uuid
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class AuditLog(models.Model):
    """
    Системный журнал сквозного аудита изменений.
    Соответствует разделу 12.1 ER-модели v1.1.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Кто совершил действие
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="Пользователь"
    )
    
    # Тип операции (например: PROJECT_CREATED, OUTPUT_DEADLINE_CHANGED)
    action = models.CharField(max_length=255, verbose_name="Действие")
    
    # Полиморфная связь Generic Relation с любым объектом системы
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(verbose_name="ID объекта")
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Хранение состояния до и после изменений
    old_value = models.JSONField(blank=True, null=True, verbose_name="Старое значение")
    new_value = models.JSONField(blank=True, null=True, verbose_name="Новое значение")
    
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP-адрес")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at} | {self.user} -> {self.action}"