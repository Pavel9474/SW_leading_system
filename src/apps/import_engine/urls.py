from django.urls import path
from . import views

app_name = 'import_engine'

urlpatterns = [
    path('wizard/', views.import_wizard, name='wizard'),
    path('preview/', views.upload_and_preview, name='preview'),
    path('confirm/', views.confirm_project, name='confirm'),
]