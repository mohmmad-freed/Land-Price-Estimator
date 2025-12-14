from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .models import Project


User = get_user_model()

def dashboard(request):
    return render(request, 'Normal_User_Side/dashboard.html')



def profile(request,pk):
    user = User.objects.get(id = pk)
    return render(request, 'Normal_User_Side/profile.html')

def editProfile(request,pk):
    user = User.objects.get(id = pk)
    return render(request, 'Normal_User_Side/edit_profile.html')


def newProject(request):
     infrastructures = ["Water", "Electricity", "Internet", "Road Access"]
     Restrictions = ["Residential Only", "Commercial Allowed", "Industrial Restricted"]
     context = {'infrastructures': infrastructures, 'Restrictions': Restrictions}
     return render(request, 'Normal_User_Side/new_project.html', context)


def viewProjects(request):
     projects = Project.objects.all().order_by('-date_created')
     context = {
        'projects': projects,
        'land_types': Project.LAND_TYPES,
        'political_types': Project.POLITICAL,
        'statuses': Project.STATUS_CHOICES,
    }
     return render(request, 'Normal_User_Side/projects.html',context)


def settings(request):
     return render(request, 'Normal_User_Side/settings.html')


