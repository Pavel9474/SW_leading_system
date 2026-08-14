import uuid
from django.db import models
from django.conf import settings

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Руководитель")

class Stage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stages')
    status = models.CharField(max_length=20, default='in_progress')
    
    # Хранение снимка незакрытых "хвостов" при принудительном закрытии этапа
    warnings = models.JSONField(null=True, blank=True, verbose_name="Предупреждения при закрытии")
    closed_at = models.DateTimeField(null=True, blank=True)

class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='tasks')

class Output(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='outputs')
    status = models.CharField(max_length=20, default='in_progress')