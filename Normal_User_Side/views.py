from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .ml.predict import predict_land_price
from .models import Project
from django.contrib.auth.decorators import login_required
from .forms import UserForm, ProjectForm


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
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user

            if request.POST.get('action') == 'estimate':
                input_data = {
                    "governorate": project.governorate,
                    "land_size": project.land_size,
                    "land_type": project.land_type,
                    "political_classification": project.political_classification,
                    
                }
                try:
                    project.estimated_price = predict_land_price(input_data)
                    project.status = 'completed'
                except Exception as e:
                    messages.error(request, "Price estimation failed. Please try again later.")
                    project.status = 'draft'
            else:
                project.status = 'draft'

            project.save()
            return redirect('normal_user:projects')

    else:
        form = ProjectForm()

    return render(request, 'Normal_User_Side/new_project.html', {'form': form})


def viewProjects(request):
     projects = Project.objects.filter(user=request.user).order_by('-date_created')
      # Get filter parameters from GET request
     land_type = request.GET.get('land_type')
     political_type = request.GET.get('political_type')
     status = request.GET.get('status')
     search_query = request.GET.get('search')

    # Apply filters in the view
     if land_type:
        projects = projects.filter(land_type=land_type)
     if political_type:
        projects = projects.filter(political_classification=political_type)
     if status:
        projects = projects.filter(status=status)
     if search_query:
        projects = projects.filter(name__icontains=search_query)
     context = {
        'projects': projects,
        'land_types': Project.LAND_TYPES,
        'political_types': Project.POLITICAL,
        'statuses': Project.STATUS_CHOICES,
    }
     return render(request, 'Normal_User_Side/projects.html',context)


def settings(request):
     return render(request, 'Normal_User_Side/settings.html')