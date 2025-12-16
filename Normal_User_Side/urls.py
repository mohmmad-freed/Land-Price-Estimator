from django.urls import path 
from . import views

app_name = 'normal_user'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/<int:pk>/', views.profile, name='profile'),
    path('edit-profile/', views.editProfile, name='edit-profile'),
    path('new-project/', views.newProject, name='new-project'),
    path('projects/', views.viewProjects, name='projects'),
    path('settings/', views.settings, name='settings'),
   
]