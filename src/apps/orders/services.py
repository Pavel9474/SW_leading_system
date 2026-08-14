from datetime import date
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.orders.models import Order, Assignment
from apps.audit.services import log_action


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(*, actor, title: str, executor, deadline: date, project=None, output=None, description: str = '') -> Order:
        if deadline < date.today():
            raise ValidationError({"deadline": "Дата deadline не может быть в прошлом."})

        if output:
            is_legitimate = Assignment.objects.filter(user=executor, output=output).exists()
            if not is_legitimate:
                raise ValidationError({"executor": "Исполнитель не включен в состав легитимных исполнителей этого выхода."})

        order = Order.objects.create(
            title=title,
            description=description,
            issuer=actor,
            executor=executor,
            deadline=deadline,
            project=project,
            output=output,
            status=Order.Status.NEW
        )

        log_action(
            user=actor,
            action="ORDER_CREATED",
            entity=order,
            new_value={"title": title, "deadline": str(deadline), "executor_id": str(executor.id)}
        )
        return order

    @staticmethod
    @transaction.atomic
    def complete_order(*, actor, order: Order) -> Order:
        if order.status != Order.Status.SUBMITTED:
            raise ValidationError({"status": "Перевести в 'Выполнено' можно только поручение в статусе 'submitted'."})
        
        if order.issuer != actor:
            raise ValidationError({"actor": "Принять работу может только сотрудник, выдавший поручение."})

        old_status = order.status
        order.status = Order.Status.COMPLETED
        order.save(update_fields=['status'])

        log_action(
            user=actor,
            action="ORDER_COMPLETED",
            entity=order,
            old_value={"status": old_status},
            new_value={"status": order.status}
        )
        return order

    @staticmethod
    @transaction.atomic
    def refuse_order(*, actor, order: Order, reason: str) -> Order:
        if order.status not in [Order.Status.NEW, Order.Status.IN_PROGRESS]:
            raise ValidationError({"status": "Отказаться можно только от новых или выполняемых поручений."})
        
        if order.executor != actor:
            raise ValidationError({"actor": "Инициатором отказа может выступать строго назначенный исполнитель."})
            
        if not reason or not reason.strip():
            raise ValidationError({"reason": "Причина отказа строго обязательна."})

        old_status = order.status
        order.status = Order.Status.REFUSED
        order.refusal_reason = reason.strip()
        order.save(update_fields=['status', 'refusal_reason'])

        log_action(
            user=actor,
            action="ORDER_REFUSED",
            entity=order,
            old_value={"status": old_status},
            new_value={"status": order.status, "reason": order.refusal_reason}
        )
        return order

    @staticmethod
    @transaction.atomic
    def return_order(*, actor, order: Order, comment: str) -> Order:
        if order.status != Order.Status.SUBMITTED:
            raise ValidationError({"status": "Возврат возможен только из статуса 'submitted'."})
            
        if order.issuer != actor:
            raise ValidationError({"actor": "Инициатором возврата может выступать только автор поручения."})
            
        if not comment or not comment.strip():
            raise ValidationError({"comment": "Комментарий строго обязателен."})

        old_status = order.status
        order.status = Order.Status.RETURNED
        order.save(update_fields=['status'])

        log_action(
            user=actor,
            action="ORDER_RETURNED",
            entity=order,
            old_value={"status": old_status},
            new_value={"status": order.status, "comment": comment.strip()}
        )
        return order


order_service = OrderService()