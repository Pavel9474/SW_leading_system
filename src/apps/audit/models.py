import uuid
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):
    """
    Системный журнал сквозного аудита изменений.
    Соответствует разделу 12.1 ER-модели v1.1 с поддержкой Celery enrichment.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Ожидает обработки'
        PROCESSED = 'PROCESSED', 'Обработано'
        FAILED = 'FAILED', 'Ошибка обработки'

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

    action = models.CharField(max_length=255, db_index=True, verbose_name="Действие")

    # Полиморфная связь Generic Relation (опциональная для гибкости)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Тип контента"
    )
    object_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="ID объекта"
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # Поля для фильтрации и асинхронного enrichment
    target_content_type = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="Тип целевого объекта"
    )
    target_object_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="ID целевого объекта"
    )

    # Метаданные состояния
    old_value = models.JSONField(blank=True, null=True, verbose_name="Старое значение")
    new_value = models.JSONField(blank=True, null=True, verbose_name="Новое значение")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Метаданные (JSONB)")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Статус обработки"
    )

    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP-адрес")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Дата и время")

    # ------------------------------------------------------------------
    # Properties (Алиасы для полной совместимости с API / Selector)
    # ------------------------------------------------------------------
    @property
    def actor(self):
        return self.user

    @actor.setter
    def actor(self, value):
        self.user = value

    @property
    def timestamp(self):
        return self.created_at

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} | {self.user} -> {self.action}"