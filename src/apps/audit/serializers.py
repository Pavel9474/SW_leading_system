from rest_framework import serializers
from apps.audit.models import AuditLog
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditActorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name']

    def get_name(self, obj):
        full_name = f"{obj.last_name} {obj.first_name} {getattr(obj, 'patronymic', '')}".strip()
        return full_name or obj.username


class AuditLogSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source='timestamp', format='%Y-%m-%dT%H:%M:%S%z')
    actor = AuditActorSerializer(read_only=True)
    entity_type = serializers.CharField(source='target_content_type')
    entity_id = serializers.CharField(source='target_object_id')
    metadata = serializers.JSONField(source='payload')

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'created_at',
            'actor',
            'action',
            'entity_type',
            'entity_id',
            'metadata',
        ]