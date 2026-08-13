from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from src.apps.audit.models import AuditLog

User = get_user_model()


class AuditAPITests(APITestCase):
    def setUp(self):
        # Создаем пользователей с разными ролями
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='password123'
        )
        self.user_a = User.objects.create_user(
            username='user_a', email='usera@test.com', password='password123', first_name='Иван', last_name='Иванов'
        )
        self.user_b = User.objects.create_user(
            username='user_b', email='userb@test.com', password='password123', first_name='Петр', last_name='Петров'
        )

        # Создаем тестовые записи аудита
        self.log_a = AuditLog.objects.create(
            actor=self.user_a,
            action='OUTPUT_COMPLETED',
            target_content_type='output',
            target_object_id='uuid-1',
            payload={'status': 'completed'}
        )
        self.log_b = AuditLog.objects.create(
            actor=self.user_b,
            action='PROJECT_CREATED',
            target_content_type='project',
            target_object_id='uuid-2',
            payload={'title': 'Project B'}
        )

        self.url = reverse('audit-list')

    def test_unauthenticated_user_gets_401(self):
        response = self.client.get(self.url)
        # DRF возвращает 401 или 403 в зависимости от схемы аутентификации
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_user_sees_only_own_events(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'OUTPUT_COMPLETED')

    def test_admin_sees_all_events(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_action(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?action=OUTPUT_COMPLETED")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'OUTPUT_COMPLETED')

    def test_filter_by_entity_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?entity_id=uuid-2")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['entity_id'], 'uuid-2')

    def test_entity_history_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        entity_url = reverse('audit-entity-history', kwargs={'entity_type': 'output', 'entity_id': 'uuid-1'})
        response = self.client.get(entity_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['entity_id'], 'uuid-1')

    def test_empty_filter_returns_200_with_empty_list(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"{self.url}?action=NON_EXISTENT_ACTION")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])