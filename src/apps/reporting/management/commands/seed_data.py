import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.organization.models import Employee, Department, Position, DepartmentMembership
from apps.projects.models import Project
from apps.workflow.models import Stage, Task, Output
from apps.assignments.models import Assignment

class Command(BaseCommand):
    help = 'Наполнение базы данных НИР начальными тестовыми данными v1.1'

    def handle(self, *args, **options):
        self.stdout.write("Начало генерации демонстрационных данных...")
        
        with transaction.atomic():
            # 1. Создание системных пользователей
            u_manager, _ = User.objects.get_or_create(username="manager_pavel", email="pavel.m@inst.ru")
            u_manager.set_password("secure_pass123")
            u_manager.save()

            u_emp1, _ = User.objects.get_or_create(username="petrov_ii", email="petrov.ii@inst.ru")
            u_emp2, _ = User.objects.get_or_create(username="ivanov_ss", email="ivanov.ss@inst.ru")

            # 2. Создание профилей сотрудников
            mgr_profile, _ = Employee.objects.get_or_create(
                user=u_manager, defaults={"first_name": "Павел", "last_name": "Руководителев"}
            )
            petrov_profile, _ = Employee.objects.get_or_create(
                user=u_emp1, defaults={"first_name": "Иван", "last_name": "Петров", "middle_name": "Иванович"}
            )
            ivanov_profile, _ = Employee.objects.get_or_create(
                user=u_emp2, defaults={"first_name": "Сергей", "last_name": "Иванов"}
            )

            # 3. Создание оргструктуры (Институт -> Отделы/Лаборатории)
            institute, _ = Department.objects.get_or_create(name="Научно-исследовательский Институт Ядерной Физики", short_name="НИИ ЯФ")
            lab_doz, _ = Department.objects.get_or_create(name="Лаборатория радиационной дозиметрии", short_name="ЛРД", parent=institute)
            dept_med, _ = Department.objects.get_or_create(name="Отделение ядерной медицины", short_name="ОЯМ", parent=institute)

            # 4. Создание справочника должностей
            pos_chief, _ = Position.objects.get_or_create(name="Заведующий лабораторией", short_name="Зав. лаб.")
            pos_res, _ = Position.objects.get_or_create(name="Старший научный сотрудник", short_name="СНС")

            # 5. Привязка сотрудников к подразделениям (Моделируем Совмещение!)
            # Петров И.И. — Основное место: СНС в Лаборатории дозиметрии (ЛРД)
            mem_petrov_primary, _ = DepartmentMembership.objects.get_or_create(
                employee=petrov_profile, department=lab_doz, position=pos_res,
                defaults={"is_primary": True}
            )
            # Петров И.И. — Совместительство: СНС в Отделении ядерной медицины (ОЯМ)
            mem_petrov_secondary, _ = DepartmentMembership.objects.get_or_create(
                employee=petrov_profile, department=dept_med, position=pos_res,
                defaults={"is_primary": False}
            )
            # Иванов С.С. — Только в Лаборатории дозиметрии (ЛРД)
            mem_ivanov, _ = DepartmentMembership.objects.get_or_create(
                employee=ivanov_profile, department=lab_doz, position=pos_res,
                defaults={"is_primary": True}
            )

            # 6. Создание тестового проекта НИР
            project, _ = Project.objects.get_or_create(
                name="Исследование воздействия изотопов нового поколения на биологические маркеры",
                project_type="grant",
                defaults={
                    "status": "in_progress",
                    "manager": mgr_profile,
                    "start_date": timezone.now().date(),
                    "end_date": timezone.now().date() + timezone.timedelta(days=365)
                }
            )
            project.members.add(petrov_profile, ivanov_profile)

            # 7. Структура работ: Этап -> Задача
            stage, _ = Stage.objects.get_or_create(
                project=project, name="Этап 1. Дозиметрическое планирование",
                defaults={"start_date": timezone.now().date(), "end_date": timezone.now().date() + timezone.timedelta(days=90)}
            )
            task, _ = Task.objects.get_or_create(
                stage=stage, name="Задача 1.1. Калибровка датчиков и сбор первичных метрик",
                defaults={"start_date": timezone.now().date(), "end_date": timezone.now().date() + timezone.timedelta(days=45)}
            )

            # 8. Результаты (Выходы НИР)
            out_1, _ = Output.objects.get_or_create(
                task=task, name="Протокол калибровки детекторов ЛРД",
                defaults={"output_type": "Отчет", "status": "in_progress", "deadline": timezone.now().date() + timezone.timedelta(days=30)}
            )
            out_2, _ = Output.objects.get_or_create(
                task=task, name="Статья по результатам дозиметрии изотопов в ОЯМ",
                defaults={"output_type": "Статья", "status": "in_progress", "deadline": timezone.now().date() + timezone.timedelta(days=45)}
            )

            # 9. Архитектурное назначение исполнителей (с привязкой к роли)
            # Назначаем Петрова на выход 1 ОТ ИМЕНИ ЛАБОРАТОРИИ ДОЗИМЕТРИИ
            Assignment.objects.get_or_create(
                output=out_1, employee=petrov_profile, department_membership=mem_petrov_primary,
                defaults={"is_responsible": True}
            )
            # Назначаем Петрова на выход 2 ОТ ИМЕНИ ОТДЕЛЕНИЯ ЯДЕРНОЙ МЕДИЦИНЫ
            Assignment.objects.get_or_create(
                output=out_2, employee=petrov_profile, department_membership=mem_petrov_secondary,
                defaults={"is_responsible": True}
            )

        self.stdout.write(self.style.SUCCESS("Тестовые данные v1.1 успешно сгенерированы!"))