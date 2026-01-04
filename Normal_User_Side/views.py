from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
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
            # Determine status based on the button clicked
            action = request.POST.get('action')
            if action == 'save':
                project.status = 'draft'
            elif action == 'estimate':
                project.status = 'completed'
                # Here you can call your ML model to estimate the price
                # e.g., project.price = estimate_price(project)

            project.save()

            # Optionally redirect after saving
            return redirect('normal_user:projects') 
    else:
        form = ProjectForm()
     

    context = {'form':form}
    return render(request, 'Normal_User_Side/new_project.html', context)


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


