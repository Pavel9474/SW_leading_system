from datetime import datetime
from typing import Optional
from django.db.models import QuerySet, Q
from apps.audit.models import AuditLog


class AuditSelector:
    @staticmethod
    def get_audit_logs(
        actor,
        action: Optional[str] = None,
        target_user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> QuerySet[AuditLog]:
        """
        Возвращает фильтрованный QuerySet с учетом ролевой области видимости (Scope) пользователя.
        """
        qs = AuditLog.objects.select_related('user').all()

        # 1. Иерархическая область видимости (Scope)
        if actor.is_superuser or getattr(actor, 'role', None) == 'ADMIN':
            pass
        elif getattr(actor, 'role', None) == 'GENERAL_DIRECTOR':
            pass
        elif getattr(actor, 'role', None) == 'DIRECTOR':
            institute_id = getattr(actor, 'institute_id', None)
            qs = qs.filter(
                Q(user__institute_id=institute_id) |
                Q(target_content_type__icontains='institute', target_object_id=str(institute_id))
            )
        elif getattr(actor, 'role', None) == 'DEPARTMENT_HEAD':
            department_id = getattr(actor, 'department_id', None)
            qs = qs.filter(
                Q(user__department_id=department_id) |
                Q(target_content_type__icontains='department', target_object_id=str(department_id))
            )
        elif getattr(actor, 'role', None) == 'LAB_HEAD':
            lab_id = getattr(actor, 'lab_id', None)
            qs = qs.filter(
                Q(user__lab_id=lab_id) |
                Q(target_content_type__icontains='lab', target_object_id=str(lab_id))
            )
        elif getattr(actor, 'role', None) == 'PROJECT_MANAGER':
            managed_project_ids = list(actor.managed_projects.values_list('id', flat=True))
            qs = qs.filter(
                Q(user=actor) |
                Q(target_content_type__icontains='project', target_object_id__in=[str(pid) for pid in managed_project_ids])
            )
        else:
            qs = qs.filter(user=actor)  # Используем поле user вместо actor

        # 2. Пользовательские фильтры
        if action:
            qs = qs.filter(action=action)

        if target_user_id:
            qs = qs.filter(user_id=target_user_id)

        if entity_type:
            qs = qs.filter(target_content_type__iexact=entity_type)

        if entity_id:
            qs = qs.filter(target_object_id=str(entity_id))

        if date_from:
            qs = qs.filter(created_at__gte=date_from)

        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        return qs.order_by('-created_at')  # Используем поле created_at вместо timestamp


audit_selector = AuditSelector()