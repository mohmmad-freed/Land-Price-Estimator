from django.contrib import admin
from django.urls import path, include


from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('normal/', include('Apps.Normal_User_Side.urls', namespace='normal')),
    path('scientist/', include('Apps.Data_Scientist_Side.urls', namespace='data_scientist')),
    path('admins/', include('Apps.Admin_Side.urls', namespace='admin_side')),
    path('', include('Apps.Users_Handling_App.urls', namespace='users')),
]
