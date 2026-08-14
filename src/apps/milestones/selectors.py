from django.contrib.contenttypes.models import ContentType
from apps.milestones.models import Output
from apps.orders.models import Order
from apps.documents.models import Document

def verify_stage_readiness(*, stage_id: str) -> dict:
    """
    Агрегирует интегральный показатель готовности вехи/этапа.
    """
    # Все Выходы, относящиеся к задачам данного этапа
    outputs = Output.objects.filter(task__stage_id=stage_id)
    
    # 1. Количество незавершенных Выходов
    uncompleted_outputs_count = outputs.exclude(status='completed').count()
    
    # 2. Количество незавершенных Поручений
    # Связываем Поручения (Order) с Выходами (Output) через ID
    uncompleted_orders_count = Order.objects.filter(
        output_id__in=outputs.values_list('id', flat=True)
    ).exclude(status='completed').count()
    
    # 3. Проверка наличия загруженных документов для завершенных Выходов
    completed_outputs = outputs.filter(status='completed')
    output_ct = ContentType.objects.get_for_model(Output)
    
    # Ищем ID тех Выходов, к которым прикреплен хотя бы один документ
    outputs_with_docs = Document.objects.filter(
        content_type=output_ct,
        object_id__in=completed_outputs.values_list('id', flat=True)
    ).values_list('object_id', flat=True)
    
    # Разница — это завершенные Выходы БЕЗ прикрепленных файлов
    missing_documents_outputs = list(
        completed_outputs.exclude(id__in=outputs_with_docs).values_list('id', flat=True)
    )
    
    is_perfect = (
        uncompleted_outputs_count == 0 and 
        uncompleted_orders_count == 0 and 
        len(missing_documents_outputs) == 0
    )
    
    return {
        "stage_id": str(stage_id),
        "is_perfect": is_perfect,
        "uncompleted_outputs_count": uncompleted_outputs_count,
        "uncompleted_orders_count": uncompleted_orders_count,
        "missing_documents_outputs": [str(uid) for uid in missing_documents_outputs]
    }