from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
# from .models import 


User = get_user_model()

def dashboard(request):
    return render(request, 'Normal_User_Side/dashboard.html')



def profile(request,pk):
    user = User.objects.get(id = pk)
    return render(request, 'Normal_User_Side/profile.html')


def newProject(request):
     infrastructures = ["Water", "Electricity", "Internet", "Road Access"]
     Restrictions = ["Residential Only", "Commercial Allowed", "Industrial Restricted"]
     context = {'infrastructures': infrastructures, 'Restrictions': Restrictions}
     return render(request, 'Normal_User_Side/new_project.html', context)


def viewProjects(request):
     return render(request, 'Normal_User_Side/projects.html')


def settings(request):
     return render(request, 'Normal_User_Side/settings.html')


