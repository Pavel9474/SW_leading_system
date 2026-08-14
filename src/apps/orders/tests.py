from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from apps.orders.models import Order, DummyOutput, Assignment
from apps.orders.services import order_service
from apps.audit.models import AuditLog

User = get_user_model()

class OrderServiceTests(TestCase):
    def setUp(self):
        self.issuer = User.objects.create_user(username='issuer')
        self.executor = User.objects.create_user(username='executor')
        self.hacker = User.objects.create_user(username='hacker')
        
        self.output = DummyOutput.objects.create()
        # Добавляем легитимную связь для исполнителя
        Assignment.objects.create(user=self.executor, output=self.output)

    def test_create_order_past_deadline_fails(self):
        past_date = date.today() - timedelta(days=1)
        with self.assertRaisesMessage(ValidationError, "Дата deadline не может быть в прошлом."):
            order_service.create_order(
                actor=self.issuer, 
                title="Test", 
                executor=self.executor, 
                deadline=past_date
            )

    def test_create_order_unauthorized_executor_fails(self):
        # hacker не имеет Assignment на этот output
        future_date = date.today() + timedelta(days=5)
        with self.assertRaisesMessage(ValidationError, "Исполнитель не включен в состав легитимных исполнителей"):
            order_service.create_order(
                actor=self.issuer, 
                title="Test", 
                executor=self.hacker, 
                deadline=future_date,
                output=self.output
            )

    def test_create_order_success_and_audit(self):
        future_date = date.today() + timedelta(days=5)
        order = order_service.create_order(
            actor=self.issuer, 
            title="Success", 
            executor=self.executor, 
            deadline=future_date,
            output=self.output
        )
        
        self.assertEqual(order.status, Order.Status.NEW)
        self.assertTrue(AuditLog.objects.filter(action="ORDER_CREATED", object_id=str(order.id)).exists())

    def test_complete_order_permissions(self):
        order = Order.objects.create(title="T", issuer=self.issuer, executor=self.executor, deadline=date.today(), status=Order.Status.SUBMITTED)
        
        # Только issuer может завершить
        with self.assertRaisesMessage(ValidationError, "Принять работу может только сотрудник, выдавший поручение."):
            order_service.complete_order(actor=self.executor, order=order)
            
        completed_order = order_service.complete_order(actor=self.issuer, order=order)
        self.assertEqual(completed_order.status, Order.Status.COMPLETED)
        self.assertTrue(AuditLog.objects.filter(action="ORDER_COMPLETED", object_id=str(order.id)).exists())

    def test_refuse_order_validation(self):
        order = Order.objects.create(title="T", issuer=self.issuer, executor=self.executor, deadline=date.today(), status=Order.Status.NEW)
        
        # Ошибка пустого комментария
        with self.assertRaisesMessage(ValidationError, "Причина отказа строго обязательна."):
            order_service.refuse_order(actor=self.executor, order=order, reason="   ")
            
        refused_order = order_service.refuse_order(actor=self.executor, order=order, reason="Слишком мало времени")
        self.assertEqual(refused_order.status, Order.Status.REFUSED)
        self.assertEqual(refused_order.refusal_reason, "Слишком мало времени")
        self.assertTrue(AuditLog.objects.filter(action="ORDER_REFUSED", object_id=str(order.id)).exists())

    def test_return_order_validation(self):
        order = Order.objects.create(title="T", issuer=self.issuer, executor=self.executor, deadline=date.today(), status=Order.Status.SUBMITTED)
        
        with self.assertRaisesMessage(ValidationError, "Комментарий строго обязателен."):
            order_service.return_order(actor=self.issuer, order=order, comment="")
            
        returned_order = order_service.return_order(actor=self.issuer, order=order, comment="Переделать раздел 2")
        self.assertEqual(returned_order.status, Order.Status.RETURNED)
        self.assertTrue(AuditLog.objects.filter(action="ORDER_RETURNED", object_id=str(order.id)).exists())