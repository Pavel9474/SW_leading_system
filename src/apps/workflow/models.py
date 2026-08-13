import uuid
from django.db import models
from django.core.exceptions import ValidationError

class Stage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='stages',
        verbose_name="Проект"
    )
    name = models.CharField(max_length=255, verbose_name="Название этапа")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    
    status = models.CharField(
        max_length=20, 
        choices=[('active', 'В работе'), ('completed', 'Завершен')], 
        default='active', 
        verbose_name="Статус"
    )

    class Meta:
        db_table = 'stages'
        verbose_name = 'Этап проекта'
        verbose_name_plural = 'Этапы проектов'

    def __str__(self):
        return f"{self.name} ({self.project.name[:20]})"


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="Этап НИР"
    )
    name = models.CharField(max_length=255, verbose_name="Название задачи")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")

    class Meta:
        db_table = 'tasks'
        verbose_name = 'Задача НИР'
        verbose_name_plural = 'Задачи НИР'

    def __str__(self):
        return self.name


class Output(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('submitted', 'На проверке'),
        ('returned', 'На доработке'),
        ('completed', 'Выполнен'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='outputs',
        verbose_name="Задача НИР"
    )
    name = models.CharField(max_length=255, verbose_name="Название выхода")
    output_type = models.CharField(max_length=100, verbose_name="Тип выхода (Отчет/Статья/Патент)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    deadline = models.DateField(verbose_name="Срок сдачи")

    class Meta:
        db_table = 'outputs'
        verbose_name = 'Выход (Результат)'
        verbose_name_plural = 'Выходы (Результаты)'

    def __str__(self):
        return f"{self.name} — {self.get_status_display()}"