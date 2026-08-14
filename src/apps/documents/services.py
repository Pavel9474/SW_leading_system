from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from apps.documents.models import Document, DocumentVersion

# Правильный импорт только функции log_action
from apps.audit.services import log_action


class DocumentService:
    @staticmethod
    @transaction.atomic
    def upload_document(*, actor, entity, file, name: str) -> Document:
        """
        Первичная загрузка: создание документа и его первой версии.
        """
        content_type = ContentType.objects.get_for_model(entity)
        
        document = Document.objects.create(
            name=name,
            content_type=content_type,
            object_id=entity.id
        )
        
        version = DocumentVersion.objects.create(
            document=document,
            file=file,
            version_number=1,
            author=actor
        )

        log_action(
            user=actor,
            action="DOCUMENT_UPLOADED",
            entity=document,
            new_value={
                "name": name,
                "version": 1,
                "entity_type": content_type.model,
                "entity_id": str(entity.id)
            }
        )

        return document

    @staticmethod
    @transaction.atomic
    def create_document_version(*, actor, document: Document, file) -> DocumentVersion:
        """
        Создание новой версии существующего документа.
        """
        latest_version = document.versions.order_by('-version_number').first()
        next_version = (latest_version.version_number + 1) if latest_version else 1
        
        version = DocumentVersion.objects.create(
            document=document,
            file=file,
            version_number=next_version,
            author=actor
        )

        log_action(
            user=actor,
            action="DOCUMENT_VERSION_UPLOADED",
            entity=document,
            new_value={
                "name": document.name,
                "new_version": next_version
            }
        )

        return version

    @staticmethod
    @transaction.atomic
    def delete_document(*, actor, document: Document):
        """
        Удаление документа.
        """
        log_action(
            user=actor,
            action="DOCUMENT_DELETED",
            entity=document,
            old_value={"name": document.name}
        )
        
        document.delete()


document_service = DocumentService()