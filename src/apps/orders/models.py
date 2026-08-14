import uuid
from django.db import models
from django.conf import settings

# TODO: Замените эти импорты на реальные модели из ваших приложений проектов и рабочих процессов
class DummyProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

class DummyOutput(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

class Assignment(models.Model):
    """Связка легитимных исполнителей с результатами (Выходами)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    output = models.ForeignKey(DummyOutput, on_delete=models.CASCADE, related_name='assignments')


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новое'
        IN_PROGRESS = 'in_progress', 'В работе'
        SUBMITTED = 'submitted', 'На проверке'
        COMPLETED = 'completed', 'Выполнено'
        REFUSED = 'refused', 'Отказ'
        RETURNED = 'returned', 'На доработке'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    issuer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='issued_orders')
    executor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='executed_orders')
    
    deadline = models.DateField(verbose_name="Срок исполнения")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    refusal_reason = models.TextField(blank=True, verbose_name="Причина отказа")

    project = models.ForeignKey(DummyProject, on_delete=models.SET_NULL, null=True, blank=True)
    output = models.ForeignKey(DummyOutput, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'