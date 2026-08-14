from rest_framework import serializers
from apps.documents.models import Document, DocumentVersion
from apps.audit.serializers import AuditActorSerializer

class DocumentVersionSerializer(serializers.ModelSerializer):
    author = AuditActorSerializer(read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'version_number', 'file', 'author', 'created_at']
        read_only_fields = ['id', 'version_number', 'author', 'created_at']

class DocumentSerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()
    versions_count = serializers.IntegerField(source='versions.count', read_only=True)
    
    # Поля для создания
    model_name = serializers.CharField(write_only=True, help_text="Например: 'project', 'output'")
    object_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'name', 'model_name', 'object_id', 
            'created_at', 'updated_at', 'latest_version', 'versions_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_latest_version(self, obj):
        latest = obj.versions.first()
        if latest:
            return DocumentVersionSerializer(latest).data
        return None