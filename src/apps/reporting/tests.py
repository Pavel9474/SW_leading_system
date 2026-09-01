from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User
from apps.organization.models import Employee, Department, Position, DepartmentMembership
from apps.projects.models import Project
from apps.workflow.models import Stage, Task, Output
from apps.assignments.models import Assignment
from apps.reporting.selectors import get_department_load

class DepartmentLoadSelectorTestCase(TestCase):
    """
    Тест-кейс для проверки правильности агрегации нагрузки на подразделение
    и отсутствия двойного учета выходов сотрудников-совместителей.
    """
    def setUp(self):
        # 1. Создаем тестовых пользователей и профили
        self.manager_user = User.objects.create(username="mgr", email="mgr@inst.ru")
        self.employee_user = User.objects.create(username="petrov", email="petrov@inst.ru")
        
        self.manager = Employee.objects.create(user=self.manager_user, first_name="Павел", last_name="Иванов")
        self.employee = Employee.objects.create(user=self.employee_user, first_name="Иван", last_name="Петров")
        
        # 2. Создаем два разных подразделения
        self.lab_doz = Department.objects.create(name="Лаборатория дозиметрии", short_name="ЛРД")
        self.dept_med = Department.objects.create(name="Отделение ядерной медицины", short_name="ОЯМ")
        
        self.position = Position.objects.create(name="Научный сотрудник")
        
        # 3. Оформляем Петрова как совместителя в обоих подразделениях
        self.mem_primary = DepartmentMembership.objects.create(
            employee=self.employee, department=self.lab_doz, position=self.position, is_primary=True
        )
        self.mem_secondary = DepartmentMembership.objects.create(
            employee=self.employee, department=self.dept_med, position=self.position, is_primary=False
        )
        
        # 4. Создаем проект, задачу и выходы
        self.project = Project.objects.create(
            name="Тестовый грант", project_type="grant", status="in_progress",
            manager=self.manager, start_date=timezone.now().date(), end_date=timezone.now().date()
        )
        self.stage = Stage.objects.create(project=self.project, name="Этап 1", start_date=timezone.now().date(), end_date=timezone.now().date())
        self.task = Task.objects.create(stage=self.stage, name="Задача 1", start_date=timezone.now().date(), end_date=timezone.now().date())
        
        self.out_lrd = Output.objects.create(task=self.task, name="Выход ЛРД", output_type="Отчет", status="in_progress", deadline=timezone.now().date())
        self.out_oyam = Output.objects.create(task=self.task, name="Выход ОЯМ", output_type="Статья", status="in_progress", deadline=timezone.now().date())

    def test_department_load_excludes_cross_appointments(self):
        """
        Проверка: селектор ЛРД должен видеть только выход, привязанный к членству в ЛРД,
        не дублируя данные из ОЯМ.
        """
        # Назначаем Петрова на первый выход от имени ЛРД
        Assignment.objects.create(output=self.out_lrd, employee=self.employee, department_membership=self.mem_primary)
        # Назначаем Петрова на второй выход от имени ОЯМ
        Assignment.objects.create(output=self.out_oyam, employee=self.employee, department_membership=self.mem_secondary)
        
        # Вызываем селектор для Лаборатории дозиметрии (ЛРД)
        lrd_load = get_department_load(department_id=str(self.lab_doz.id))
        
        # Убеждаемся, что агрегированное количество активных выходов для ЛРД строго равно 1, а не 2
        self.assertEqual(lrd_load["aggregated_active_outputs"], 1)
        # Убеждаемся, что в деталях сотрудника внутри ЛРД числится ровно 1 выход
        self.assertEqual(lrd_load["employees_detail"][0]["active_outputs"], 1)