import os
from celery import Celery

# Устанавливаем дефолтный модуль настроек Django для утилиты celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')

app = Celery('system_v1')

# Используем строку конфигурации, где все настройки для Celery
# будут иметь префикс CELERY_ в settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи (tasks.py) во всех зарегистрированных приложениях Django.
app.autodiscover_tasks()