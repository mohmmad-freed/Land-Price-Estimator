from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.loginPage, name='login'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('register/', views.register, name='register'),
]