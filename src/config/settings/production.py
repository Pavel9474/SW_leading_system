from .base import *

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