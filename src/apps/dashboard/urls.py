from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('widget/department-load/', views.lazy_department_load, name='lazy_department_load'),
]