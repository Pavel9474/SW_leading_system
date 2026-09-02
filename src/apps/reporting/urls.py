from django.urls import path
from apps.reporting.views import department_load_page, department_load_fragment
from . import views

app_name = 'reporting'

urlpatterns = [
    # Ваши предыдущие маршруты (модуль загрузки подразделений)
    path('department-load/', views.department_load_page, name='department_load'),
    path('department-load/fragment/', views.department_load_fragment, name='department_load_fragment'),

    # Новые маршруты (дашборд руководителя)
    path('management/', views.management_dashboard_view, name='management_dashboard'),
    path('management/financial-overview/', views.financial_overview_widget, name='financial_overview'),
    path('management/critical-alerts/', views.critical_alerts_widget, name='critical_alerts'),
]