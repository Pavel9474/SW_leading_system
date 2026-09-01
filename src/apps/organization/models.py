import uuid
from django.db import models
from django.conf import settings

class Employee(models.Model):
    """Профиль сотрудника. Связан 1:1 с учетной записью User."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee',
        verbose_name="Учетная запись"
    )
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    middle_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Отчество")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Телефон")
    is_active = models.BooleanField(default=True, verbose_name="Активность сотрудника")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    class Meta:
        db_table = 'employees'
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Department(models.Model):
    """Подразделение с поддержкой древовидной иерархии."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Название")
    short_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Сокращенное название")
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='children',
        verbose_name="Родительское подразделение"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активность")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    class Meta:
        db_table = 'departments'
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'

    def __str__(self):
        return self.short_name or self.name


class Position(models.Model):
    """Справочник должностей."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, verbose_name="Название должности")
    short_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Сокращенное название")
    is_active = models.BooleanField(default=True, verbose_name="Активность")

    class Meta:
        db_table = 'positions'
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

    def __str__(self):
        return self.name


class DepartmentMembership(models.Model):
    """Принадлежность сотрудника к подразделению (обеспечивает множественное совмещение)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Сотрудник"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Подразделение"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Должность"
    )
    is_primary = models.BooleanField(default=True, verbose_name="Основное место работы")
    valid_from = models.DateField(blank=True, null=True, verbose_name="Действует с")
    valid_to = models.DateField(blank=True, null=True, verbose_name="Действует по")

    class Meta:
            db_table = 'department_memberships'
            # Составной индекс для селекторов дашборда и отчетов
            indexes = [
                models.Index(fields=['employee', 'department', 'is_primary']),
            ]

    def __str__(self):
        return f"{self.employee} — {self.department} ({self.position})"