import random
import string
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.import_engine.parser_docx import DocxProjectParser
from apps.import_engine.parser_excel import ExcelStaffParser

User = get_user_model()


def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))


@transaction.atomic
def create_preview_project(*, actor, file) -> dict:
    """Сервис предварительного парсинга ТЗ Word с разметкой достоверности."""
    parser = DocxProjectParser(file)
    return parser.parse()


@transaction.atomic
def import_staff_structure(*, actor, file) -> dict:
    """Транзакционный сервис импорта штатного расписания с синхронизацией оргструктуры и разрешением конфликтов совмещения."""
    parser = ExcelStaffParser(file)
    valid_rows, errors = parser.parse()

    created_users_count = 0
    updated_users_count = 0
    created_departments_count = 0
    processed_rows = len(valid_rows)

    from apps.organization.models import Department, Position, DepartmentMembership, Employee

    for row in valid_rows:
        email = row["email"]
        login = row["login"]
        last_name = row["last_name"]
        first_name = row["first_name"]
        middle_name = row["middle_name"]
        is_primary = row["is_primary"]

        # Блок А: Синхронизация пользователя и профиля Employee
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": login,
                "first_name": first_name,
                "last_name": last_name,
            }
        )

        if created:
            user.set_password(generate_random_password())
            user.save()
            created_users_count += 1
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            updated_users_count += 1

        employee, _ = Employee.objects.get_or_create(
            user=user,
            defaults={"middle_name": middle_name}
        )
        if middle_name and employee.middle_name != middle_name:
            employee.middle_name = middle_name
            employee.save()

        # Блок Б: Синхронизация оргструктуры (иерархия подразделений и должностей)
        parent_dept = None
        current_dept = None
        for dept_name in row["departments"]:
            current_dept, dept_created = Department.objects.get_or_create(
                name=dept_name,
                parent=parent_dept
            )
            if dept_created:
                created_departments_count += 1
            parent_dept = current_dept

        position, _ = Position.objects.get_or_create(name=row["position"])

        # Блок В: Разрешение конфликтов совмещения и автоматический сброс флага is_primary
        if is_primary:
            DepartmentMembership.objects.filter(employee=employee, is_primary=True).update(is_primary=False)

        membership, membership_created = DepartmentMembership.objects.get_or_create(
            employee=employee,
            department=current_dept,
            position=position,
            defaults={"is_primary": is_primary}
        )
        if not membership_created and membership.is_primary != is_primary:
            membership.is_primary = is_primary
            membership.save()

    return {
        "status": "success",
        "processed_rows": processed_rows,
        "created_users_count": created_users_count,
        "updated_users_count": updated_users_count,
        "created_departments_count": created_departments_count,
        "errors": errors
    }