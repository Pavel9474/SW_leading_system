from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_page, name='profile'),
    path('order/<uuid:order_id>/submit/', views.submit_order_from_profile, name='submit_order'),
    # Новые маршруты для Выходов НИР
    path('output/<uuid:output_id>/attach-modal/', views.attach_output_modal, name='attach_output_modal'),
    path('output/<uuid:output_id>/attach/', views.attach_output_file, name='attach_output_file'),
]