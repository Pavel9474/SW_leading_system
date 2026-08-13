import uuid
from django.db import models
from django.conf import settings

class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('planned', 'Запланирован'),
        ('in_progress', 'В работе'),
        ('review', 'На приемке'),
        ('completed', 'Завершен'),
    ]

    TYPE_CHOICES = [
        ('tz', 'По техническому заданию'),
        ('grant', 'Грант'),
        ('contract', 'Договор / Контракт'),
        ('internal', 'Внутренний научный проект'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(verbose_name="Название проекта")
    project_type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="Тип проекта")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    
    manager = models.ForeignKey(
        'organization.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects',
        verbose_name="Руководитель проекта"
    )
    members = models.ManyToManyField(
        'organization.Employee',
        related_name='projects',
        verbose_name="Участники проекта",
        blank=True
    )
    
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    def __str__(self):
        return f"{self.name[:50]}... ({self.get_status_display()})"