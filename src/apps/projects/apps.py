from django.apps import AppConfig

class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'
    label = 'projects_app'  # Явно задаем уникальную метку (label), чтобы избежать конфликтов
    verbose_name = 'Управление проектами'