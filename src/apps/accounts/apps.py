from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.accounts'  # Явно указываем путь внутри папки src
    verbose_name = 'Управление пользователями'