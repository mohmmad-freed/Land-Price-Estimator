from django.urls import path 
from . import views

app_name = 'normal'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/<int:pk>/', views.profile, name='profile'),
    path('edit-profile/', views.editProfile, name='edit-profile'),
    path('new-project/', views.newProject, name='new-project'),
    path('projects/', views.viewProjects, name='projects'),
    path('normal/new-project/<int:project_id>/', views.newProject, name='new-project'),
    path('projects/delete/<int:project_id>/', views.deleteProject, name='delete-project'),
    
    # API endpoints for cascading dropdowns
    path('api/towns/', views.get_towns, name='api-towns'),
    path('api/areas/', views.get_areas, name='api-areas'),
    path('api/neighborhoods/', views.get_neighborhoods, name='api-neighborhoods'),
    path('api/neighborhood-code/', views.get_neighborhood_code, name='api-neighborhood-code'),
    path('api/predict-price/', views.api_predict_price, name='api-predict-price'),
    path('api/confirm-prediction/', views.api_confirm_prediction, name='api-confirm-prediction'),
]