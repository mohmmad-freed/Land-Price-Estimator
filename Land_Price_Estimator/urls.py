from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('normal/', include('Normal_User_Side.urls', namespace='normal_user')),
    path('scientist/', include('Data_Scientist_Side.urls', namespace='data_scientist')),
    path('admin/', include('Admin_Side.urls', namespace='admin_side')),
    path('users/', include('Users_Handling_App.urls')),
]
