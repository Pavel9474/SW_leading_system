from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import Document, DocumentVersion
from apps.audit.models import AuditLog

User = get_user_model()

class DocumentAPITests(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='doc_user', 
            password='password123',
            first_name='Иван',
            last_name='Иванов'
        )
        self.list_url = reverse('document-list')
    
    def test_unauthenticated_access_denied(self):
        """Проверка защиты роутов от анонимов"""
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_upload_new_document(self):
        """Проверка первичной загрузки документа и создания записи в аудите"""
        self.client.force_authenticate(user=self.user)
        
        # Имитируем файл PDF
        test_file = SimpleUploadedFile("test_doc.pdf", b"dummy content", content_type="application/pdf")
        
        data = {
            'name': 'Техническое задание v1',
            'model_name': 'user',  # Привязываем к пользователю для теста
            'object_id': self.user.id,
            'file': test_file
        }
        
        response = self.client.post(self.list_url, data, format='multipart')
        
        # 1. Проверяем API
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['versions_count'], 1)
        
        # 2. Проверяем БД
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(DocumentVersion.objects.count(), 1)
        
        doc = Document.objects.first()
        self.assertEqual(doc.name, 'Техническое задание v1')
        self.assertEqual(doc.content_type.model, 'user')
        
        # 3. Проверяем Аудит
        audit_exists = AuditLog.objects.filter(
            action="DOCUMENT_UPLOADED", 
            object_id=str(doc.id) # <--- ИСПРАВЛЕНО
        ).exists()
        self.assertTrue(audit_exists, "Событие создания документа не зафиксировано в аудите")

    def test_upload_document_version(self):
        """Проверка загрузки новой версии файла"""
        self.client.force_authenticate(user=self.user)
        
        # Создаем первый документ (v1)
        test_file_v1 = SimpleUploadedFile("test_v1.pdf", b"version 1 content", content_type="application/pdf")
        response_v1 = self.client.post(self.list_url, {
            'name': 'План работ',
            'model_name': 'user',
            'object_id': self.user.id,
            'file': test_file_v1
        }, format='multipart')
        
        doc_id = response_v1.data['id']
        
        # Загружаем вторую версию (v2)
        version_url = reverse('document-upload-version', kwargs={'pk': doc_id})
        test_file_v2 = SimpleUploadedFile("test_v2.pdf", b"version 2 updated content", content_type="application/pdf")
        
        response_v2 = self.client.post(version_url, {'file': test_file_v2}, format='multipart')
        
        # 1. Проверяем, что версия стала второй
        self.assertEqual(response_v2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_v2.data['version_number'], 2)
        
        # 2. Проверяем БД: документ остался 1, а версий стало 2
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(DocumentVersion.objects.count(), 2)
        
        # 3. Проверяем Аудит
        audit_exists = AuditLog.objects.filter(
            action="DOCUMENT_VERSION_UPLOADED",  # <--- Должно быть это действие
            object_id=str(doc_id)                # <--- Здесь doc_id (через нижнее подчеркивание)
        ).exists()
        self.assertTrue(audit_exists, "Событие обновления версии не зафиксировано в аудите")

    def test_document_history(self):
        """Проверка эндпоинта истории версий (сортировка по убыванию)"""
        self.client.force_authenticate(user=self.user)
        
        # Загружаем v1
        test_file_v1 = SimpleUploadedFile("v1.txt", b"v1")
        response = self.client.post(self.list_url, {
            'name': 'Отчет',
            'model_name': 'user',
            'object_id': self.user.id,
            'file': test_file_v1
        }, format='multipart')
        doc_id = response.data['id']
        
        # Загружаем v2
        self.client.post(reverse('document-upload-version', kwargs={'pk': doc_id}), {
            'file': SimpleUploadedFile("v2.txt", b"v2")
        }, format='multipart')
        
        # Запрашиваем историю
        history_url = reverse('document-history', kwargs={'pk': doc_id})
        history_response = self.client.get(history_url)
        
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history_response.data), 2)
        
        # Ожидаем сортировку от новых к старым (-version_number)
        self.assertEqual(history_response.data[0]['version_number'], 2)
        self.assertEqual(history_response.data[1]['version_number'], 1)