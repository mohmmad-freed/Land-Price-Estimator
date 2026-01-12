from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .ml.predict import predict_land_price
from core.models import Project
from django.contrib.auth.decorators import login_required
from .forms import UserForm, ProjectForm, ProjectRoadFormSet



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
        road_formset = ProjectRoadFormSet(request.POST)
        
        if form.is_valid() and road_formset.is_valid():
            # Save the project but don't commit yet (need to set created_by)
            project = form.save(commit=False)
            project.created_by = request.user
            
            # Determine status based on action button clicked
            action = request.POST.get('action')
            if action == 'complete':
                project.status = 'COMPLETED'
            else:
                project.status = 'DRAFT'
            
            # Save the project to get an ID
            project.save()
            
            # Save many-to-many relationships
            # Land uses
            land_uses = form.cleaned_data.get('land_uses')
            if land_uses:
                for land_use in land_uses:
                    from core.models import ProjectLandUse
                    ProjectLandUse.objects.create(
                        project=project,
                        land_use_type=land_use
                    )
            
            # Facilities
            facilities = form.cleaned_data.get('facilities')
            if facilities:
                for facility in facilities:
                    from core.models import ProjectFacility
                    ProjectFacility.objects.create(
                        project=project,
                        facility_type=facility
                    )
            
            # Environmental factors
            environmental_factors = form.cleaned_data.get('environmental_factors')
            if environmental_factors:
                for factor in environmental_factors:
                    from core.models import ProjectEnvironmentalFactor
                    ProjectEnvironmentalFactor.objects.create(
                        project=project,
                        environmental_factor_type=factor
                    )
            
            # Save roads formset
            road_formset.instance = project
            road_formset.save()
            
            # Show success message
            if action == 'complete':
                messages.success(request, f'Project "{project.project_name}" has been created and marked as completed!')
            else:
                messages.success(request, f'Project "{project.project_name}" has been saved as draft!')
            
            return redirect('normal_user:projects')
        else:
            # Form has errors, will be displayed in template
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectForm()
        road_formset = ProjectRoadFormSet()

    context = {
        'form': form,
        'road_formset': road_formset,
    }
    return render(request, 'Normal_User_Side/new_project.html', context)


def viewProjects(request):
     projects = Project.objects.filter(created_by=request.user)
      # Get filter parameters from GET request
     land_type = request.GET.get('land_type')
     political_type = request.GET.get('political_type')
     status = request.GET.get('status')
     search_query = request.GET.get('search')
     sort_by = request.GET.get('sort', '-created_at')

    # Apply filters in the view
     if land_type:
        projects = projects.filter(land_type=land_type)
     if political_type:
        projects = projects.filter(political_classification=political_type)
     if status:
        projects = projects.filter(status=status)
     if search_query:
        projects = projects.filter(project_name__icontains=search_query)
     
     # Apply sorting
     if sort_by in ['created_at', '-created_at']:
         projects = projects.order_by(sort_by)
     else:
         projects = projects.order_by('-created_at')

     context = {
        'projects': projects,
        'land_types': Project.LandType.choices,
        'political_types': Project.PoliticalClassification.choices,
        'statuses': Project.Status.choices,
    }
     return render(request, 'Normal_User_Side/projects.html',context)


def settings(request):
     return render(request, 'Normal_User_Side/settings.html')