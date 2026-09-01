from datetime import date
from django.db.models import Q
from apps.orders.models import Order, Assignment
from apps.milestones.models import Output

def get_dashboard_context(*, user) -> dict:
    context = {
        "user": user,
        "is_manager": False,
        "executor_metrics": {},
        "manager_metrics": {}
    }

    if not user.is_authenticated:
        return context

    # Имитация проверки на руководителя. 
    # В реальности здесь: DepartmentMembership.objects.filter(user=user, role__in=['head', 'director']).exists()
    is_manager = user.groups.filter(name='Руководители').exists() or user.is_superuser
    context["is_manager"] = is_manager

    today = date.today()

    if is_manager:
        # МЕТРИКИ РУКОВОДИТЕЛЯ
        orders_submitted = Order.objects.filter(issuer=user, status=Order.Status.SUBMITTED).count()
        outputs_submitted = Output.objects.filter(status='submitted').count()
        
        critical_orders = Order.objects.select_related('issuer', 'executor', 'project'  # <--- Жадная загрузка связанных объектов
        ).filter(
            issuer=user,
            status__in=[Order.Status.NEW, Order.Status.IN_PROGRESS, Order.Status.RETURNED]
        ).order_by('deadline')[:5]

        context["manager_metrics"] = {
            "orders_submitted": orders_submitted,
            "outputs_submitted": outputs_submitted,
            "critical_orders": critical_orders,
        }
    else:
        # МЕТРИКИ ИСПОЛНИТЕЛЯ
        assigned_outputs_ids = Assignment.objects.filter(user=user).values_list('output_id', flat=True)
        active_outputs_count = Output.objects.filter(
            id__in=assigned_outputs_ids, 
            status__in=['in_progress', 'returned']
        ).count()

        active_orders = Order.objects.select_related(
            'issuer', 'executor', 'project'  # <--- Жадная загрузка связанных объектов
        ).filter(
            executor=user, 
            status__in=[Order.Status.NEW, Order.Status.IN_PROGRESS, Order.Status.RETURNED]
        ).order_by('deadline')

        overdue_orders_count = active_orders.filter(deadline__lt=today).count()

        context["executor_metrics"] = {
            "active_outputs_count": active_outputs_count,
            "active_orders": active_orders[:5],
            "overdue_orders_count": overdue_orders_count
        }

    return context