from django.contrib import messages
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum
from .ml.predict import predict_land_price
from core.models import Project, ProjectRoad
from django.contrib.auth.decorators import login_required
from .forms import UserForm, ProjectForm, ProjectRoadFormSet
from django.db.models import F



User = get_user_model()

@login_required
def dashboard(request):
    recent_projects = Project.objects.filter(created_by=request.user).order_by('-created_at')[:6]

    # Prepare values for template
    for project in recent_projects:
        # Convert Decimals to floats
        project.estimated_price_float = float(project.estimated_price or 0)
        project.area_m2_float = float(project.area_m2 or 0)
        # Pre-calculate total value to avoid arithmetic in template
        project.total_estimated_value = project.estimated_price_float * project.area_m2_float

    completed_count = Project.objects.filter(created_by=request.user, status='COMPLETED').count()
    draft_count = Project.objects.filter(created_by=request.user, status='DRAFT').count()
    total_estimated_price = sum(p.total_estimated_value for p in recent_projects)

    context = {
        'recent_projects': recent_projects,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'total_estimated_price': total_estimated_price,
    }
    return render(request, 'Normal_User_Side/dashboard.html', context)


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

@login_required
def newProject(request, project_id=None):
    """
    Create or edit a project.
    Roads: only 'road_status' and 'width_m', start empty.
    Remove road checkbox sets defaults for ML model.
    Parcel price is calculated as estimated_price * area_m2
    """
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        is_edit = True
    else:
        project = None
        is_edit = False

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        road_formset = ProjectRoadFormSet(request.POST, instance=project)

        if form.is_valid() and road_formset.is_valid():
            # Save parent project first
            project = form.save(commit=False)
            if not is_edit:
                project.created_by = request.user

            action = request.POST.get('action')
            project.status = 'COMPLETED' if action == 'complete' else 'DRAFT'
            project.save()  # parent must exist before saving related objects

            # Save roads (only road_status & width_m)
            for road_form in road_formset:
                road_data = road_form.cleaned_data
                if road_data:
                    if road_data.get('DELETE', False):
                        road = road_form.instance
                        road.road_status = 'FALSE'
                        road.width_m = 0
                        road.project = project
                        road.save()
                    else:
                        road = road_form.save(commit=False)
                        road.project = project
                        road.save()

            # Predict price if project is completed
            if action == 'complete':
                predicted_price = predict_land_price(project, road_formset)
                project.estimated_price = predicted_price
                project.save(update_fields=['estimated_price', 'status'])
                parcel_price = predicted_price * (project.area_m2 or 0)
                messages.success(
                    request,
                    f'Project "{project.project_name}" saved and completed! '
                    f'Estimated price per m²: {predicted_price:.0f} k JOD, '
                    f'Parcel price: {parcel_price:.0f} k JOD'
                )
            else:
                project.save(update_fields=['status'])
                messages.success(
                    request,
                    f'Project "{project.project_name}" saved as draft!'
                )

            return redirect('normal_user:projects')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        # GET request: initialize form & road formset
        form = ProjectForm(instance=project)
        road_formset = ProjectRoadFormSet(
            instance=project,
            queryset=ProjectRoad.objects.filter(project=project, deleted_at__isnull=True) 
                     if project else ProjectRoad.objects.none()
        )

    context = {
        'form': form,
        'road_formset': road_formset,
        'is_edit': is_edit,
        'project': project,
    }

    return render(request, 'Normal_User_Side/new_project.html', context)





@login_required
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



