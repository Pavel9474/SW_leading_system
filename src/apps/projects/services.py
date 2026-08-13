from django.core.exceptions import ValidationError
from django.db import transaction
from src.apps.projects.models import Project
from src.apps.organization.models import Employee

def create_project(
    *,
    actor: Employee,
    name: str,
    project_type: str,
    start_date,
    end_date,
    members: list[Employee],
    manager: Employee = None,
    **optional_fields
) -> Project:
    """
    Бизнес-сервис создания научно-исследовательского проекта.
    """
    # 1. Проверка прав пользователя (actor) создавать проект
    # (В v1.0 базовое ограничение, далее расширяется через permissions.py)
    if not actor.is_active:
        raise ValidationError("У пользователя нет прав на создание проекта.")

    # 2. Проверка валидности дат
    if start_date >= end_date:
        raise ValidationError("Дата начала проекта не может быть позже или равна дате окончания.")

    # 3. Проверка наличия хотя бы одного участника/исполнителя
    if not members and not manager:
        raise ValidationError("В проекте должен быть указан как минимум один участник или руководитель.")

    # Выполняем операцию атомарно внутри транзакции
    with transaction.atomic():
        project = Project.objects.create(
            name=name,
            project_type=project_type,
            start_date=start_date,
            end_date=end_date,
            manager=manager,
            status='draft',  # Начальный статус всегда Черновик
            **optional_fields
        )
        
        # Добавляем участников
        if members:
            project.members.add(*members)
            
        # Также автоматически добавляем менеджера в состав участников проекта
        if manager and manager not in members:
            project.members.add(manager)

        # ТУТ БУДЕТ ВЫЗОВ: audit.log(...) и event_bus.publish(ProjectCreated(...))
        
        return project