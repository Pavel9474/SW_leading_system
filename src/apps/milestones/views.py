from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError

from apps.milestones.models import Stage
from apps.milestones.selectors import verify_stage_readiness
from apps.milestones.services import milestone_service
from apps.audit.models import AuditLog


def stage_review_page(request, stage_id):
    """GET: Страница аудита и проверки этапа перед закрытием"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    # Получаем срез готовности
    readiness = verify_stage_readiness(stage_id=stage.id)
    
    context = {
        'stage': stage,
        'readiness': readiness,
    }
    return render(request, 'milestones/stage_review.html', context)


def close_stage_action(request, stage_id):
    """POST (HTMX): Обработчик нажатия на кнопку закрытия этапа"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    # Берем пользователя (если используете профили, то getattr(request.user, 'employee', request.user))
    actor = request.user 
    
    try:
        # Вызываем жесткую бизнес-логику
        stage = milestone_service.close_stage(actor=actor, stage=stage)
        
        # Если успешно, берем срез готовности из сохраненных предупреждений (или пересобираем)
        readiness = stage.warnings if stage.warnings else verify_stage_readiness(stage_id=stage.id)
        
        # Достаем ID лога из аудита для красивого вывода
        audit_log = AuditLog.objects.filter(action="STAGE_CLOSED", object_id=str(stage.id)).first()
        
        return render(request, 'milestones/partials/readiness_card.html', {
            'stage': stage,
            'readiness': readiness,
            'audit_log': audit_log
        })
        
    except ValidationError as e:
        # Формируем читаемый текст ошибки из словаря DRF ValidationError
        error_msgs = []
        if isinstance(e.detail, dict):
            for v in e.detail.values():
                error_msgs.append(str(v[0]) if isinstance(v, list) else str(v))
        else:
            error_msgs.append(str(e.detail))
            
        error_text = " ".join(error_msgs)
        
        # Возвращаем кусок HTML с ошибкой в стиле Tailwind
        html = f"""
        <div id="readiness-panel" class="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded shadow-sm">
            <p class="text-sm font-medium text-red-700">Ошибка валидации:</p>
            <p class="text-sm text-red-600 mt-1">{error_text}</p>
            <div class="mt-4">
                <button onclick="location.reload()" class="text-sm underline text-red-800 hover:text-red-900">
                    Обновить страницу
                </button>
            </div>
        </div>
        """
        return HttpResponse(html)