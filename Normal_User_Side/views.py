from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .models import Project
from django.contrib.auth.decorators import login_required
from .forms import UserForm


User = get_user_model()

def dashboard(request):
    return render(request, 'Normal_User_Side/dashboard.html')


@login_required(login_url='users:login')
def profile(request,pk):
    user = User.objects.get(id = pk)
    return render(request, 'Normal_User_Side/profile.html')

@login_required(login_url='users:login')
def editProfile(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save to DB yet
            new_password = form.cleaned_data.get("new_password")
            if new_password:
                 user.set_password(new_password)
            user.save()
            return redirect('normal_user:profile', pk = user.id)
    context = {"form":form}

    return render(request, 'Normal_User_Side/edit_profile.html', context)


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


