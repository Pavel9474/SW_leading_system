from .base import *
import os

DEBUG = False

# Забираем хосты из .env и превращаем в список
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Безопасность
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# При работе за Nginx, Django должен доверять заголовкам прокси
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# 1. Инициализация Sentry (только при DEBUG = False)
if not DEBUG:
    sentry_sdk.init(
        dsn=env('SENTRY_DSN', default=''),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        profiles_sample_rate=0.1,
        send_default_pii=False,  # Отключаем отправку персональных данных по умолчанию
        before_send=lambda event, hint: _sentry_data_scrubber(event),
    )

def _sentry_data_scrubber(event):
    """Фильтрация чувствительных данных (пароли, токены) перед отправкой в Sentry."""
    if 'request' in event:
        request = event['request']
        # Вырезаем потенциальные пароли или токены из заголовков и тела запроса
        if 'headers' in request:
            for header in ['Authorization', 'Cookie', 'X-CSRFToken']:
                if header in request['headers']:
                    request['headers'][header] = '[Filtered]'
        if 'data' in request and isinstance(request['data'], dict):
            for key in request['data']:
                if any(sec in key.lower() for sec in ['password', 'token', 'secret', 'key']):
                    request['data'][key] = '[Filtered]'
    return event


# 2. Ротация локальных системных логов (Django Logging)
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django_error.log',
            'maxBytes': 52428800,  # 50 МБ
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.accounts': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': True,
        },
        'apps.organization': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': True,
        },
        'apps.workflow': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': True,
        },
        'apps.audit': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}