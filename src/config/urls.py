"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    # Подключаем модуль отчетности
    path('reporting/', include('apps.reporting.urls', namespace='reporting')),
    path('api/v1/', include('apps.audit.urls')),
    path('api/v1/', include('apps.documents.urls')),
    path('milestones/', include('apps.milestones.urls', namespace='milestones')),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('import/', include('apps.import_engine.urls', namespace='import_engine')),
    
    # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: перенаправление с главной страницы на мониторинг нагрузки
    path('', RedirectView.as_view(url='/reporting/department-load/', permanent=False)),
]
