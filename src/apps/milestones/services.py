from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.milestones.models import Stage
from apps.milestones.selectors import verify_stage_readiness
from apps.audit.services import log_action

class MilestoneService:
    @staticmethod
    @transaction.atomic
    def close_stage(*, actor, stage: Stage) -> Stage:
        # 1. Валидация прав: только руководитель проекта может закрыть этап
        if stage.project.manager != actor:
            raise ValidationError({"actor": "Закрыть этап может только руководитель проекта."})
            
        # 2. Защита от повторного закрытия
        if stage.status == 'completed':
            raise ValidationError({"status": "Этот этап уже закрыт."})
            
        # 3. Анализ готовности (поиск "хвостов")
        readiness_snapshot = verify_stage_readiness(stage_id=stage.id)
        
        # 4. Изменение состояния
        old_status = stage.status
        stage.status = 'completed'
        stage.closed_at = timezone.now()
        
        # Если есть проблемы, сохраняем их в карточке этапа (для истории)
        if not readiness_snapshot['is_perfect']:
            stage.warnings = readiness_snapshot
            
        stage.save(update_fields=['status', 'closed_at', 'warnings'])
        
        # 5. Сквозной аудит
        log_action(
            user=actor,
            action="STAGE_CLOSED",
            entity=stage,
            old_value={"status": old_status},
            new_value={
                "status": "completed",
                "readiness_snapshot": readiness_snapshot
            }
        )
        
        return stage

milestone_service = MilestoneService()