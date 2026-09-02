from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_page, name='profile'),
    # Подключаем стандартные login, logout и сброс паролей внутрь namespace accounts
    path('', include('django.contrib.auth.urls')),
]