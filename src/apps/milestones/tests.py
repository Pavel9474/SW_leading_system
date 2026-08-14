from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from apps.milestones.models import Project, Stage, Task, Output
# ИСПРАВЛЕНИЕ: Импортируем DummyOutput из orders под алиасом
from apps.orders.models import Order, DummyOutput as OrderDummyOutput 
from apps.milestones.services import milestone_service
from apps.audit.models import AuditLog

User = get_user_model()

class MilestoneServiceTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='pm_user')
        self.other_user = User.objects.create_user(username='executor')
        
        # Строим иерархию проекта
        self.project = Project.objects.create(manager=self.manager)
        self.stage = Stage.objects.create(project=self.project, status='in_progress')
        self.task = Task.objects.create(stage=self.stage)
        self.output = Output.objects.create(task=self.task, status='in_progress')
        
        # ИСПРАВЛЕНИЕ: Создаем фиктивную запись в DummyOutput с тем же ID, 
        # чтобы удовлетворить строгость внешних ключей базы данных.
        OrderDummyOutput.objects.create(id=self.output.id)

        # Создаем зависшее поручение (status=NEW)
        self.order = Order.objects.create(
            title="Срочная аналитика",
            issuer=self.manager,
            executor=self.other_user,
            deadline=date.today(),
            output_id=self.output.id
        )

    def test_close_stage_unauthorized(self):
        """Проверка: Не-руководитель не может закрыть этап"""
        with self.assertRaisesMessage(ValidationError, "Закрыть этап может только руководитель проекта."):
            milestone_service.close_stage(actor=self.other_user, stage=self.stage)

    def test_close_stage_with_uncompleted_order_generates_warnings(self):
        """Проверка закрытия этапа с хвостами и корректность AuditLog"""
        closed_stage = milestone_service.close_stage(actor=self.manager, stage=self.stage)
        
        # 1. Проверяем статус и дату
        self.assertEqual(closed_stage.status, 'completed')
        self.assertIsNotNone(closed_stage.closed_at)
        
        # 2. Проверяем формирование отчета о хвостах (warnings)
        self.assertFalse(closed_stage.warnings['is_perfect'])
        self.assertEqual(closed_stage.warnings['uncompleted_outputs_count'], 1)
        self.assertEqual(closed_stage.warnings['uncompleted_orders_count'], 1)
        
        # 3. Проверяем Сквозной Аудит
        audit_exists = AuditLog.objects.filter(
            action="STAGE_CLOSED", 
            object_id=str(self.stage.id)
        ).exists()
        self.assertTrue(audit_exists, "Событие STAGE_CLOSED не зафиксировано в аудите!")