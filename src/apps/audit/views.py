from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from apps.audit.serializers import AuditLogSerializer
from apps.audit.selectors import audit_selector
from apps.audit.permissions import CanViewAuditLogsPermission


class AuditPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [CanViewAuditLogsPermission]
    pagination_class = AuditPagination

    def get_queryset(self):
        # Чтение строго определенных Query-параметров
        params = self.request.query_params
        
        return audit_selector.get_audit_logs(
            actor=self.request.user,
            action=params.get('action'),
            target_user_id=params.get('user'),
            entity_type=params.get('entity_type'),
            entity_id=params.get('entity_id'),
            date_from=params.get('date_from'),
            date_to=params.get('date_to'),
        )

    @action(detail=False, methods=['get'], url_path='entity/(?P<entity_type>[^/.]+)/(?P<entity_id>[^/.]+)')
    def entity_history(self, request, entity_type=None, entity_id=None):
        """
        Эндпоинт для истории конкретного объекта:
        GET /api/v1/audit/entity/<entity_type>/<entity_id>/
        """
        qs = audit_selector.get_audit_logs(
            actor=request.user,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)