import uuid
import os
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


def document_upload_path(instance, filename):
    # Путь: media/documents/<doc_id>/v<version>/<filename>
    return f'documents/{instance.document.id}/v{instance.version_number}/{filename}'


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Наименование документа')
    
    # Полиморфная связь
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(verbose_name='ID связанного объекта')
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        db_table = 'documents'
        # Быстрый поиск всех документов, привязанных к сущности
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return self.name


class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        related_name='versions',
        verbose_name='Документ'
    )
    file = models.FileField(upload_to=document_upload_path, verbose_name='Файл')
    version_number = models.PositiveIntegerField(verbose_name='Номер версии')
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='Автор правки'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        db_table = 'document_versions'
        verbose_name = 'Версия документа'
        verbose_name_plural = 'Версии документов'
        unique_together = ('document', 'version_number')
        ordering = ['-version_number']

    def __str__(self):
        return f'{self.document.name} (v{self.version_number})'