from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType

from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer, DocumentVersionSerializer
from apps.documents.services import document_service


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.prefetch_related('versions__author').all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        """ Загрузка нового документа """
        name = request.data.get('name')
        file_obj = request.FILES.get('file')
        model_name = request.data.get('model_name')
        object_id = request.data.get('object_id')

        if not all([name, file_obj, model_name, object_id]):
            return Response(
                {"detail": "Обязательные поля: name, file, model_name, object_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Получаем ContentType (например, app_label='projects', model='project')
            # Для простоты ищем модель по названию в рамках проекта
            content_type = ContentType.objects.get(model=model_name.lower())
            entity = content_type.model_class().objects.get(id=object_id)
        except (ContentType.DoesNotExist, AttributeError, Exception):
            return Response({"detail": "Связанный объект не найден"}, status=status.HTTP_404_NOT_FOUND)

        doc = document_service.upload_document(
            actor=request.user,
            entity=entity,
            file=file_obj,
            name=name
        )

        serializer = self.get_serializer(doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """ Удаление документа """
        document = self.get_object()
        document_service.delete_document(actor=request.user, document=document)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='versions')
    def upload_version(self, request, pk=None):
        """ Добавление новой версии к существующему документу """
        document = self.get_object()
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response({"file": "Файл обязателен."}, status=status.HTTP_400_BAD_REQUEST)

        version = document_service.create_document_version(
            actor=request.user,
            document=document,
            file=file_obj
        )
        
        return Response(DocumentVersionSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """ Получение истории версий """
        document = self.get_object()
        versions = document.versions.all()
        serializer = DocumentVersionSerializer(versions, many=True)
        return Response(serializer.data)