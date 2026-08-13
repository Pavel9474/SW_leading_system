from django.urls import path
from src.apps.reporting.views import department_load_page, department_load_fragment

app_name = 'reporting'

urlpatterns = [
    # Главная страница мониторинга
    path('department-load/', department_load_page, name='department_load_page'),
    
    # URL, к которому обращается HTMX при выборе элемента в селекторе
    path('department-load-fragment/', department_load_fragment, name='department_load_fragment'),