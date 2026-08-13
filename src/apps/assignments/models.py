import uuid
from django.db import models

class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    output = models.ForeignKey(
        'workflow.Output',
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="Выход (Результат)"
    )
    
    employee = models.ForeignKey(
        'organization.Employee',
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="Сотрудник"
    )
    
    # Ключевое архитектурное исправление: явная привязка к членству в подразделении
    department_membership = models.ForeignKey(
        'organization.DepartmentMembership',
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name="Кадровая роль (Подразделение и должность)"
    )
    
    is_responsible = models.BooleanField(
        default=False, 
        verbose_name="Ответственный исполнитель"
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата назначения")

    class Meta:
        db_table = 'assignments'
        verbose_name = 'Назначение исполнителя'
        verbose_name_plural = 'Назначения исполнителей'
        # Один сотрудник в рамках одной роли не может быть назначен на один выход дважды
        unique_together = ('output', 'employee', 'department_membership')

    def __str__(self):
        status = "Ответственный" if self.is_responsible else "Исполнитель"
        return f"{self.employee} ({self.department_membership.department.short_name}) — {status}"