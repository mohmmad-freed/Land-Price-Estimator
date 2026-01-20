from django.urls import path
from . import views

app_name = 'data_scientist'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.editProfile, name='edit-profile'),
    # ML Model Management
    path('models/', views.model_list, name='model_list'),
    path('models/upload/', views.model_upload, name='model_upload'),
    path('models/<int:model_id>/', views.model_detail, name='model_detail'),
    path('models/<int:model_id>/activate/', views.model_activate, name='model_activate'),
    # Valuation History
    path('valuations/', views.valuation_list, name='valuation_list'),
    # Statistics & Analytics
    path('statistics/', views.statistics, name='statistics'),
]
