from django.urls import path
from apps.milestones import views

app_name = 'milestones'

urlpatterns = [
    path('stage/<uuid:stage_id>/review/', views.stage_review_page, name='stage_review'),
    path('stage/<uuid:stage_id>/close/', views.close_stage_action, name='close_stage_action'),
]